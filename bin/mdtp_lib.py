#!/usr/bin/env python

import argparse
import re
import time

from github import Github, InputGitAuthor
from jenkinsapi.custom_exceptions import JenkinsAPIException
from jenkinsapi.jenkins import Jenkins
from requests import HTTPError

import lib


def create_git_release(job, conf):
    tagger = InputGitAuthor(conf.git_username, conf.git_email)
    github = conf.github_api
    gh = Github(base_url=github, login_or_token=conf.git_token)
    org = gh.get_organization('HMRC')
    repo = org.get_repo(job)
    # repo = gh.get_user("jose-taboada").get_repo("enron")
    commit = repo.get_commits()[0]

    if False:  # I dont know  if it's the first release...
        repo.create_git_tag_and_release("release/0.1.0", "releasing version test/0.1.0 of Enron", "release/0.1.0",
                                        "release message", commit.sha, "commit", tagger)
        return "0.1.0"
    else:
        last_tag = repo.get_tags()[0]
        current_version = re.search(r'release/\s*([\d.]+)', last_tag.name).group(1)
        newVersion = lib.read_user_preferred_version(job, current_version)
        releaseMessage = "releasing version release/{0} of vat-core".format(newVersion)
        repo.create_git_tag_and_release("release/" + newVersion, releaseMessage, "release/" + newVersion,
                                        releaseMessage, commit.sha, "commit", tagger)
        return newVersion


def run_build(job, tag, conf, verbose):
    J = Jenkins(conf.jenkins_build, conf.jenkins_user, conf.jenkins_build_key)

    if verbose:
        print "App: " + job
        print "Jenkins Version " + J.version
        print J.get_job(job).get_last_good_build()

    try:
        newJob = J.build_job(job, {"TAG": tag})
    except JenkinsAPIException, ex:
        print("Error: %s" % (ex.message))

    newJobNumber = J[job].get_last_buildnumber() + 1
    print "Job {0} is being built".format(newJobNumber)

    last_completed = J[job].get_last_completed_buildnumber()
    while (last_completed != newJobNumber):
        print "Waiting for completion of Job {0}, {1}".format(newJobNumber, last_completed)
        time.sleep(25)
        last_completed = J[job].get_last_completed_buildnumber()

    print "Job completed. Wait 30 seconds"
    # Time to WebStore
    time.sleep(30)


def execute(conf, job, args, env):


    print env.get_job(job).get_last_good_build()
    try:
        env.build_job(job, {"ARGS": args})
    except HTTPError, ex:
        print("Error?: %s" % (ex.message))

    newJobNumber = env[job].get_last_buildnumber() + 1
    print "Job {0} is being built".format(newJobNumber)

    last_completed = env[job].get_last_completed_buildnumber()
    while (last_completed != newJobNumber):
        print "Waiting for completion of Job {0}, {1}".format(newJobNumber, last_completed)
        time.sleep(5)
        last_completed = env[job].get_last_completed_buildnumber()

    output = env[job].get_build(newJobNumber).get_console()
    print output

    print "Job completed"


def deploy_qa(job, tag, conf, env):
    # QA = Jenkins(conf.jenkins_qa, conf.jenkins_user, conf.jenkins_qa_key)
    print "Deploy Microservice in QA"

    print env.get_job('deploy-microservice').get_last_good_build()

    try:
        env.build_job('deploy-microservice', {"APP": job, "VERSION": tag, "DEPLOYMENT_BRANCH": "master"})
    except HTTPError, ex:
        print("Error?: %s" % (ex.message))

    newJobNumber = env['deploy-microservice'].get_last_buildnumber() + 1
    print "Job {0} is being built".format(newJobNumber)

    last_completed = env['deploy-microservice'].get_last_completed_buildnumber()
    while (last_completed != newJobNumber):
        print "Waiting for completion of Job {0}, {1}".format(newJobNumber, last_completed)
        time.sleep(30)
        last_completed = env['deploy-microservice'].get_last_completed_buildnumber()

    print "Job (QA) completed"


def deploy_staging(job, tag, conf, env):
    microservice='deploy-microservice-multiactive'
    # Staging = Jenkins(conf.jenkins_staging, conf.jenkins_user, conf.jenkins_staging_key)
    print "Deploy Microservice in Staging " + env.version
    print "Deploy Microservice in Staging " + job
    print "Deploy Microservice in Staging {0}".format(tag)

    print env.get_job(microservice).get_last_good_build()

    try:
        env.build_job(microservice, {"APP": job, "VERSION": tag, "DEPLOYMENT_BRANCH": "master"})
    except HTTPError, ex:
        print("Error?: %s" % (ex.message))

    newJobNumber = env[microservice].get_last_buildnumber() + 1
    print "Job {0} is being built".format(newJobNumber)

    last_completed = env[microservice].get_last_completed_buildnumber()
    while (last_completed != newJobNumber):
        print "Waiting for completion of Job {0}, {1}".format(newJobNumber, last_completed)
        time.sleep(30)
        last_completed = env[microservice].get_last_completed_buildnumber()

    print "Job (Staging) completed"


def parseArguments():
    parser = argparse.ArgumentParser(description='Library release tagger - tag non-snapshot libraries')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print debug output')
    parser.add_argument('operation', type=str, help='Operation to perform: Release And Deploy OR deploy-only')
    parser.add_argument('projectName', type=str, help='The jenkins build of the repo we want to tag')
    parser.add_argument('version', nargs='?', type=str, help='The jenkins build of the repo we want to tag')
    parser.add_argument('env', nargs='?', type=str, help='Environment to deploy')
    args = parser.parse_args()
    return args


def DeployTo(env):
    print "Deploy to {0}?".format(env)
    while 1:
        try:
            choice = str(raw_input('Y/N: [Y] '))
        except ValueError:
            print "Please enter 'Y' or 'N' "
            continue
        if not choice or choice == 'Y' or choice == 'y':
            return True
        if choice == 'N' or choice == 'n':
            return False

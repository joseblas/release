#!/usr/bin/env python

from jenkinsapi.jenkins import Jenkins
import lib
import argparse
from config import Configuration
from github import Github, InputGitAuthor
import time, re
from jenkinsapi.custom_exceptions import JenkinsAPIException
from requests import HTTPError

conf = Configuration()
conf.validate()


def create_git_release(job):
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


def run_build(job, tag):
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

    print "Job completed"


def deployQA(job, tag):
    QA = Jenkins(conf.jenkins_qa, conf.jenkins_user, conf.jenkins_qa_key)
    print "Deploy Microservice in QA"

    print QA.get_job('deploy-microservice').get_last_good_build()

    try:
        QA.build_job('deploy-microservice', {"APP": job, "VERSION": tag, "DEPLOYMENT_BRANCH": "master"})
    except HTTPError, ex:
        print("Error?: %s" % (ex.message))

    newJobNumber = QA['deploy-microservice'].get_last_buildnumber() + 1
    print "Job {0} is being built".format(newJobNumber)

    last_completed = QA['deploy-microservice'].get_last_completed_buildnumber()
    while (last_completed != newJobNumber):
        print "Waiting for completion of Job {0}, {1}".format(newJobNumber, last_completed)
        time.sleep(30)
        last_completed = QA['deploy-microservice'].get_last_completed_buildnumber()

    print "Job (QA) completed"



parser = argparse.ArgumentParser(description='Library release tagger - tag non-snapshot libraries')
parser.add_argument('-v', '--verbose', action='store_true', help='Print debug output')
parser.add_argument('projectName', type=str, help='The jenkins build of the repo we want to tag')
args = parser.parse_args()


app = args.projectName
verbose=args.verbose
print app + " "
print verbose
nTag = create_git_release(app)
print "New Tag: {0}".format(nTag)
run_build(app, nTag)

print "Deploy to QA? "
while 1:
    try:
        choice = str(raw_input('Y/N: [Y] '))
    except ValueError:
        print "Please enter 'Y' or 'N' "
        continue
    if not choice or choice == 'Y' or choice == 'y':
        qa = True
        break
    if choice == 'N' or choice == 'n':
        qa = False
        break

if qa:
    print("deloying to QA")
    deployQA(app, nTag)

#!/usr/bin/env python

from mdtp_lib import *
from concurrent.futures import *
from config import Configuration

conf = Configuration()
conf.validate()

args = parseArguments()

app = args.projectName
verbose=args.verbose
operation= args.operation

print app + " " + operation
print verbose

if operation == 'release' or operation == 'deploy':
    qa = DeployTo('QA')
    staging = DeployTo('Staging')

    if operation == 'release':
        nTag = create_git_release(app, conf)
        print "New Tag: {0}".format(nTag)
        run_build(app, nTag, conf, verbose)
    else:
        nTag = args.version

    if verbose:
        print "Version to deploy/release:" + nTag

    executor = ThreadPoolExecutor(max_workers=2)

    if qa:
        print("deploying to QA")
        executor.submit(deploy_qa(app, nTag, conf))

    if staging:
        print("deploying to Staging")
        executor.submit(deploy_staging(app, nTag, conf))

if operation == 'db-status':
    qa = Jenkins(conf.jenkins_qa, conf.jenkins_user, conf.jenkins_qa_key)
    # prod = Jenkins(conf.jenkins_prod, conf.jenkins_user, conf.jenkins_prod_key)
    execute(conf, 'curl-microservice-active',"-X GET https://portal-db-test.public-monolith.mdtp/connectivity/{0}".format(app), qa)
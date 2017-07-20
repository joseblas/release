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
        nTag = create_git_release(app)
        print "New Tag: {0}".format(nTag)
        run_build(app, nTag)
    else:
        nTag = args.version

    if verbose:
        print "Version to deploy/release:" + nTag

    executor = ThreadPoolExecutor(max_workers=2)

    if qa:
        print("deploying to QA")
        executor.submit(deployQA(app, nTag))

    if staging:
        print("deploying to Staging")
        executor.submit(deployStaging(app, nTag))

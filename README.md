This project is based on the works of HMRC from
```
https://github.com/hmrc/release
```

# Improvements
 1. No need to download the project to release/tag. Done remotely in GihHub.
 2. Use of native Python Libs for GitHub and Jenkins.
 3. Creates a pipeline to tag, build and deploy the app in several Envs (only QA by now)

# Releasing an artifact

This repo provides a script that allows to tag a git repository:

It looks if the specified build completed successfully
Gets the commit id from the build
Suggests you the new version
Tags the repository
## Prepare the environment

Set up your local configuration by creating a file ~/.hmrc/release.conf which is a json formatted file that should look like this:
{
    "jenkins":"https://ci-dev...",
    "jenkins_build": "https://ci-build...",
    "jenkins_qa": "https://deploy-qa...",
    "github_api": "https://github.../api/v3",
    "git_username": "jose-taboada",
    "git_email": "jose.taboada@...",
    "git_token": "69...",
    "jenkins_user":"jose.taboada",
    "jenkins_key":"<dev-key>",
    "jenkins_build_key": "<build-key>",
    "jenkins_qa_key": "<QA-key>"
}


In addition to that you need some python libraries (setup pip and virtualenv if needed)
$ virtualenv virtual_release
$ source virtual_release/bin/activate
$ pip install -r requirements.txt

Release

./bin/mdtp.py 'app'

License

This code is open source software licensed under the Apache 2.0 License.
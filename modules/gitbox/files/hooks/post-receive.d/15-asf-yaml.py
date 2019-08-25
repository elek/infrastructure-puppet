#!/usr/bin/env python
import os
import sys
if not os.environ.get("ASFGIT_ADMIN"):
    print("Invalid server configuration.")
    sys.exit(1)
sys.path.append(os.environ["ASFGIT_ADMIN"])
import yaml
import subprocess
import asfpy.messaging
import asfgit.cfg as cfg
import asfgit.asfyaml

DEFAULT_CONTACT = 'team@infra.apache.org' # Set to none to go to default project ML

def has_feature(name):
    return callable(getattr(asfgit.asfyaml,name))

def get_yaml():
    committer = cfg.committer
    blamemail = "%s@apache.org" % committer
    main_contact = DEFAULT_CONTACT or cfg.recips[0] #commits@project or whatever is set in git config?
    
    # We just need the first line, as that has the branch affected:
    line = sys.stdin.readline().strip()
    if not line:
        return
    [oldrev, newrev, refname] = line.split()
    try:
        FNULL = open(os.devnull, 'w')
        ydata = subprocess.check_output(("/usr/bin/git", "show", "%s:.asf.yaml" % refname), stderr = FNULL)
    except:
        ydata = ""
    if not ydata:
        return
    try:
        config = yaml.safe_load(ydata)
    except yaml.YAMLError as e:
        asfpy.messaging.mail(recipients = [blamemail, main_contact], subject = "Failed to parse .asf.yaml in %s.git!" % cfg.repo_name, message = str(e))
        return
    
    if config:
        
        # Validate
        try:
            for k, v in config.iteritems():
                if not has_feature(k):
                    raise Exception("Found unknown feature entry '%s' in .asf.yaml!\nPlease fix this error ASAP.")
        except Exception as e:
            msg = str(e)
            subject = "Failed to parse .asf.yaml in %s.git!" % cfg.repo_name
            asfpy.messaging.mail(recipients = [blamemail, main_contact], subject = subject, message = msg)
            return
        
        # Run parts
        for k, v in config.iteritems():
            func = getattr(asfgit.asfyaml,k)
            func(cfg, v)

if __name__ == '__main__':        
    get_yaml()

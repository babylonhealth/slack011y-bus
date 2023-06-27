# https://circleci.com/blog/circleci-hacks-validate-circleci-config-on-every-commit-with-a-git-hook/

exec < /dev/tty

# If validation fails, tell Git to stop and provide error message. Otherwise, continue.
if ! eMSG=$(circleci config validate -c .circleci/config.yml); then
	echo "CircleCI Configuration Failed Validation."
	echo $eMSG
	exit 1
fi

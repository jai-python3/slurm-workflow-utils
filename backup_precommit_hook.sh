#!/bin/sh
echo "Going to backup pre-commit hook"
mv .git/hooks/pre-commit .git/hooks/pre-commit.bak
echo "Execute bumpversion"
echo "Push the tags like this: git push --tags"
echo "Remember to restore the pre-commit hook like this: ./restore_precommit_hook.sh"

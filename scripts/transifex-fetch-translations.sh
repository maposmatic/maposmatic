#! /bin/sh -x

# Pull translations from transifex
# Forcibly pull all translations becase git clone in a fresh repo causes the local files to
# be more recent then translations on transifex, therefore the translastion is skipped
### tx pull --force --all

# Commit any changes
# git diff

git config user.email "hakan@gurkensalat.com"
git config user.name "Hakan Tandogan"

# git add scripts/transifex-fetch-translations.sh
# git commit -m "Updated message translation fetching script" scripts/transifex-fetch-translations.sh

# Loop over all translations
for translation in $(find $(dirname $0)/../www/locale/eo -name \*.po)
do
    $(dirname $0)/../ci-scripts/transifex-commit-translations.pl ${translation}
done

# Keep Jenkins happy so it won't mark the build as failed for no reason :-(
true

# Done, git push to be done manually or from jenkins

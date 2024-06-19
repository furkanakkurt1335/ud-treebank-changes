from subprocess import run
import argparse, os, glob
from pathlib import Path

def get_args():
    parser = argparse.ArgumentParser(description='Check difference between 2 versions of a treebank')
    parser.add_argument('-t', '--treebank', type=str, help='Name of the treebank')
    parser.add_argument('-l', '--language', type=str, help='Language of the treebank')
    parser.add_argument('-v1', '--version1', type=str, help='Version 1 of the treebank')
    parser.add_argument('-v2', '--version2', type=str, help='Version 2 of the treebank')
    return parser.parse_args()

def get_changes(conllu_files):
    sentences = []
    for conllu_file in conllu_files:
        with open(conllu_file) as f:
            content = f.read().strip()
            sentences.extend(content.split('\n\n'))
    mark_count = 0
    # NOUN, ADJ, DET, INTJ should not be attached as mark
    for sentence in sentences:
        lines = sentence.split('\n')
        for line in lines:
            if line.startswith('#'):
                continue
            fields = line.split('\t')
            id_t, form, lemma, upos, xpos, feats, head, deprel, deps, misc = fields
            if deprel == 'mark' and upos in ['NOUN', 'ADJ', 'DET', 'INTJ']:
                mark_count += 1
    return mark_count

def main():
    treebank_url = 'https://github.com/UniversalDependencies/{treebank_title}.git'
    version_tag = 'r{version}'
    args = get_args()
    treebank_name, language, version1, version2 = args.treebank, args.language, args.version1, args.version2
    treebank_title = f'UD_{language}-{treebank_name}'
    script_dir = Path(__file__).parent
    treebanks_dir = script_dir / 'treebanks'
    if not treebanks_dir.exists():
        treebanks_dir.mkdir()
    treebank_dir = treebanks_dir / treebank_title
    if not treebank_dir.exists():
        print(f'{treebank_title} does not exist. Cloning...')
        run(['git', 'clone', treebank_url.format(treebank_title=treebank_title), treebank_dir])
    os.chdir(treebank_dir)

    # Checkout version 1
    run(['git', 'checkout', version_tag.format(version=version1)])

    # Get stats on what to check difference of in version 1
    conllu_files = glob.glob('*.conllu')
    stats1 = get_changes(conllu_files)

    # Checkout version 2
    run(['git', 'checkout', version_tag.format(version=version2)])

    # Get stats on what to check difference of in version 2
    conllu_files = glob.glob('*.conllu')
    stats2 = get_changes(conllu_files)

    # Print stats
    print(f'Stats for version {version1}:', stats1)
    print(f'Stats for version {version2}:', stats2)

if __name__ == '__main__':
    main()
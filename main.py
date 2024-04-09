from subprocess import check_output, run, PIPE
import json, re, os, shutil, argparse
from pathlib import Path

def get_args():
    parser = argparse.ArgumentParser(description='Download all Universal Dependencies treebanks')
    parser.add_argument('-r', '--repos', type=str, help='Path to repos.json file')
    return parser.parse_args()

def main():
    treebank_pattern = re.compile(r'UD_(.+)-(.+)')
    organization = 'UniversalDependencies'
    script_dir = Path(__file__).resolve().parent
    args = get_args()
    if args.repos:
        repos_path = Path(args.repos)
    else:
        repos_path = script_dir / 'repos.json'

    if repos_path.exists():
        with repos_path.open() as f:
            repo_d = json.load(f)
    else:
        repo_url = f'https://api.github.com/orgs/{organization}/repos?per_page=100&page='
        repos_l = []
        for page in range(1, 100):
            print(f'Getting page {page}')
            repos = json.loads(check_output(['curl', '-s', repo_url + str(page)]).decode('utf-8'))
            if not repos:
                break
            for repo in repos:
                if treebank_pattern.match(repo['name']):
                    repos_l.append(repo['name'])
            print(f'Current repo count: {len(repos_l)}')
        repos_l.sort()
        print(f'Final repo count: {len(repos_l)}')
        repo_d = {repo_name: {'tags': [], 'checked_tags': False, 'has_change': False, 'changes': {'git-diff': [], 'diff': []}, 'checked_changes': False} for repo_name in repos_l}
        with repos_path.open('w') as f:
            json.dump(repo_d, f, indent=2)

    testing_ground_dir = script_dir / 'testing_ground'
    if testing_ground_dir.exists():
        shutil.rmtree(testing_ground_dir)

    tag_pattern = re.compile(r'^r(\d+\.\d+)$')
    base_url = 'https://github.com/UniversalDependencies/{repo}.git'
    for repo, repo_info in repo_d.items():
        repo_dir = script_dir / repo
        if repo_info['checked_tags'] and repo_info['checked_changes']:
            continue
        run(['git', 'clone', base_url.format(repo=repo), repo_dir])
        os.chdir(repo_dir)

        if not repo_info['checked_tags']:
            tags = [i for i in check_output(['git', 'tag', '-l']).decode('utf-8').strip().split('\n') if i and tag_pattern.match(i)]
            repo_d[repo]['tags'] = tags
            repo_d[repo]['checked_tags'] = True

        tags = repo_d[repo]['tags']
        if not repo_info['checked_changes']:
            print(f'Checking changes for {repo}')
            tags = repo_info['tags']
            tags.sort(key=lambda x: tuple(map(int, x[1:].split('.'))))
            testing_ground_dir.mkdir()
            for tag in tags:
                tag_dir = testing_ground_dir / tag
                tag_dir.mkdir()
                run(['git', 'checkout', tag])
                conllu_files = list(repo_dir.glob('*.conllu'))
                for conllu_file in conllu_files:
                    shutil.copy(conllu_file, tag_dir)
            for i in range(len(tags)-1):
                current_tag = tags[i]
                next_tag = tags[i+1]
                changed_files = [i for i in check_output(['git', 'diff', '--name-only', f'{current_tag}..{next_tag}', '*.conllu']).decode('utf-8').strip().split('\n') if '/' not in i]
                if changed_files != ['']:
                    repo_d[repo]['has_change'] = True
                    repo_d[repo]['changes']['git-diff'].append((current_tag, next_tag, changed_files))
            for i in range(len(tags)-1):
                current_dir = testing_ground_dir / tags[i]
                current_files = set([i.name for i in current_dir.glob('*.conllu')])
                next_dir = testing_ground_dir / tags[i+1]
                next_files = set([i.name for i in next_dir.glob('*.conllu')])
                for file_name in current_files.intersection(next_files):
                    current_file = current_dir / file_name
                    next_file = next_dir / file_name
                    diff = run(['diff', str(current_file), str(next_file)], stdout=PIPE).stdout
                    line_count = check_output(['wc', '-l'], input=diff).decode('utf-8').strip().split()[0]
                    print(f'{file_name}: {line_count} lines')
                    if line_count != '0':
                        repo_d[repo]['changes']['diff'].append((tags[i], tags[i+1], file_name, line_count))
                for file_name in current_files.difference(next_files):
                    repo_d[repo]['changes']['diff'].append((tags[i], tags[i+1], file_name, 'deleted'))
                for file_name in next_files.difference(current_files):
                    repo_d[repo]['changes']['diff'].append((tags[i], tags[i+1], file_name, 'added'))
            shutil.rmtree(testing_ground_dir)
            repo_d[repo]['checked_changes'] = True

        os.chdir(script_dir)

        if repo_dir.exists():
            shutil.rmtree(repo_dir)
        with repos_path.open('w') as f:
            json.dump(repo_d, f, indent=2)

    with repos_path.open('w') as f:
        json.dump(repo_d, f, indent=2)

if __name__ == '__main__':
    main()
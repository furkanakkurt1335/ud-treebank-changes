import argparse, json, re
from pathlib import Path

def get_args():
    parser = argparse.ArgumentParser(description='Get the number of treebanks by language')
    parser.add_argument('-r', '--repos', type=str, help='Path to repos.json file')
    return parser.parse_args()

def main(args):
    repos_path = Path(args.repos)
    with repos_path.open() as f:
        repos = json.load(f)
    
    lang_tb_pattern = 'UD_(.+)-(.+)'

    lang_d = {}
    for repo in repos:
        match = re.match(lang_tb_pattern, repo)
        if match:
            lang = match.group(1)
            if lang not in lang_d:
                lang_d[lang] = []
            lang_d[lang].append(repo)
    
    lang_tb_count_path  = repos_path.parent / 'lang_tb_count.json'
    with lang_tb_count_path.open('w') as f:
        json.dump(lang_d, f, indent=4)
    
    count_d = {}
    for lang, repos in lang_d.items():
        tb_count  = len(repos)
        if tb_count not in count_d:
            count_d[tb_count] = 0
        count_d[tb_count] += 1
    
    count_path  = repos_path.parent / 'tb_count.json'
    with count_path.open('w') as f:
        json.dump(count_d, f, indent=4, sort_keys=True)
    
    print('Done')
    
if __name__ == '__main__':
    args = get_args()
    main(args)
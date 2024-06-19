import argparse, json
from pathlib import Path

def get_args():
    parser = argparse.ArgumentParser(description='Get the change quantity of versions of given treebanks')
    parser.add_argument('-r', '--repos', type=Path, help='Path to repos.json file', default=Path('repos.json'))
    parser.add_argument('-t', '--treebanks', type=Path, help='Path to treebanks.json file', default=Path('treebanks.json'))
    return parser.parse_args()

def main(args):
    repos_path = Path(args.repos)
    with repos_path.open() as f:
        repos = json.load(f)

    treebanks_path = Path(args.treebanks)
    with treebanks_path.open() as f:
        treebanks = json.load(f)
    
    tb_list = list(treebanks.keys())

    for tb in tb_list:
        versions = treebanks[tb]
        changes = repos[tb]['changes']['diff']
        change_count = 0
        for change in changes:
            v1, v2 = change[:2]
            if v1 in versions and v2 in versions:
                change_count += int(change[3])
        print(f'{tb}: {change_count}')
    
if __name__ == '__main__':
    args = get_args()
    main(args)
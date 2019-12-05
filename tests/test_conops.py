import os
import subprocess
import shlex
HERE = os.path.abspath(os.path.dirname(__file__))
CONOPS_FILE = os.path.join(HERE, 'conops.sh')
def test_conops():
    fails = []
    with open(CONOPS_FILE) as f:
        conops = f.read()

    lines = conops.splitlines()
    for line in lines:
        print('='*100)
        print(f'Calling: {line}')
        out = subprocess.run(line, shell=True,  env=os.environ)
        if out.returncode != 0:
            fails.append(line)
        print('='*100)

    print(f'{len(fails)} Commands failed')
    failed = '\n'.join(fails)
    print(f"{failed}")
    assert len(fails)==0

if __name__ == '__main__':
    test_conops()
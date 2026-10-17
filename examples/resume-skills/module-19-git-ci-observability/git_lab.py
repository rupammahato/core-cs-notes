"""Every mutation targets disposable repositories under the supplied owned directory."""
from pathlib import Path
import json,os,subprocess
from release import FILES

def run_lab(scratch):
    scratch=Path(scratch).resolve()
    repo=scratch/'git-work';remote=scratch/'remote.git';peer=scratch/'git-peer'
    repo.mkdir();hooks=scratch/'empty-hooks';hooks.mkdir()
    empty=scratch/'empty.gitconfig';empty.write_text('',encoding='utf-8')
    env={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    env.update(GIT_CONFIG_GLOBAL=str(empty),GIT_CONFIG_NOSYSTEM='1',GIT_TERMINAL_PROMPT='0',
               GIT_AUTHOR_DATE='2026-10-14T12:00:00+00:00',GIT_COMMITTER_DATE='2026-10-14T12:00:00+00:00')
    commands=[];checks=[];observations={}
    def git(args,where=repo,success=True):
        where=Path(where).resolve()
        if not where.is_relative_to(scratch):raise RuntimeError('Git target outside fixture')
        cmd=['git','-c','user.name=Placement Fixture','-c','user.email=fixture@example.test',
             '-c','commit.gpgsign=false','-c','core.autocrlf=false','-c','core.hooksPath='+str(hooks),'-C',str(where),*args]
        r=subprocess.run(cmd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=20)
        commands.append({'args':args,'repo':where.name,'code':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if success and r.returncode:raise RuntimeError(str(args)+'\n'+r.stdout+r.stderr)
        return r
    def check(name,condition,evidence=None):
        checks.append({'group':'git','name':name,'passed':bool(condition),'evidence':evidence})
        if not condition:raise AssertionError(name)
    def write(name,value):(repo/name).write_text(value,encoding='utf-8')
    def commit(message):git(['add','.']);git(['commit','-m',message]);return git(['rev-parse','HEAD']).stdout.strip()
    git(['init','-b','main'])
    write('state.txt','base\n');base=commit('Base snapshot')
    write('state.txt','staged\n');git(['add','state.txt']);write('state.txt','working\n')
    state={'head':git(['show','HEAD:state.txt']).stdout.strip(),'index':git(['show',':state.txt']).stdout.strip(),'working':(repo/'state.txt').read_text().strip()}
    check('head_index_worktree_are_distinct',state=={'head':'base','index':'staged','working':'working'},state)
    git(['restore','--staged','state.txt'])
    check('unstage_preserves_working_file',git(['show',':state.txt']).stdout=='base\n' and (repo/'state.txt').read_text()=='working\n')
    git(['restore','state.txt'])
    check('restore_worktree_uses_index',(repo/'state.txt').read_text()=='base\n')
    git(['switch','-c','feature']);write('feature.txt','feature\n');feature=commit('Feature')
    git(['switch','main']);write('main.txt','main\n');main=commit('Main independently advances')
    git(['merge','--no-ff','feature','-m','Merge independent work'])
    parents=git(['show','-s','--format=%P','HEAD']).stdout.split()
    check('merge_records_two_parent_histories',parents==[main,feature] and (repo/'feature.txt').exists(),parents)
    git(['switch','-c','conflict-side']);write('state.txt','side\n');commit('Side edits same line')
    git(['switch','main']);write('state.txt','main-edit\n');conflict_base=commit('Main edits same line')
    conflict=git(['merge','conflict-side'],success=False)
    check('conflict_stops_merge_with_unmerged_index',conflict.returncode!=0 and bool(git(['ls-files','-u']).stdout) and '<<<<<<<' in (repo/'state.txt').read_text())
    git(['merge','--abort'])
    check('abort_restores_premerge_head_and_file',git(['rev-parse','HEAD']).stdout.strip()==conflict_base and (repo/'state.txt').read_text()=='main-edit\n')
    git(['merge','conflict-side'],success=False);write('state.txt','resolved\n');resolved=commit('Resolve conflict deliberately')
    check('resolved_merge_has_two_parents',len(git(['show','-s','--format=%P','HEAD']).stdout.split())==2 and not git(['ls-files','-u']).stdout)
    git(['switch','-c','topic']);write('topic.txt','topic-patch\n');old=commit('Topic before rebase')
    old_patch=git(['diff',old+'^',old,'--','topic.txt']).stdout
    git(['switch','main']);write('advance.txt','advance\n');advance=commit('Advance main before rebase')
    git(['switch','topic']);git(['rebase','main']);new=git(['rev-parse','HEAD']).stdout.strip()
    check('rebase_replays_to_a_new_commit',old!=new and git(['show','-s','--format=%P','HEAD']).stdout.strip()==advance,{'old':old,'new':new})
    check('rebase_preserves_the_example_patch',git(['diff',new+'^',new,'--','topic.txt']).stdout==old_patch)
    write('revert-me.txt','temporary-feature\n');original=commit('Feature to revert')
    git(['revert','--no-edit',original]);reverted=git(['rev-parse','HEAD']).stdout.strip()
    check('revert_adds_inverse_without_erasing_target',reverted!=original and not (repo/'revert-me.txt').exists() and git(['merge-base','--is-ancestor',original,'HEAD']).returncode==0)
    git(['switch','main']);git(['init','--bare','-b','main',str(remote)])
    git(['remote','add','origin',str(remote)]);git(['push','-u','origin','main'])
    git(['clone',str(remote),str(peer)],where=scratch)
    old_peer=git(['rev-parse','HEAD'],where=peer).stdout.strip()
    write('remote-change.txt','remote-progress\n');remote_head=commit('New published fixture commit');git(['push','origin','main'])
    git(['fetch','origin'],where=peer)
    check('fetch_updates_tracking_ref_without_moving_head',git(['rev-parse','HEAD'],where=peer).stdout.strip()==old_peer and git(['rev-parse','origin/main'],where=peer).stdout.strip()==remote_head)
    git(['merge','--ff-only','origin/main'],where=peer)
    check('fast_forward_moves_to_existing_commit',git(['rev-parse','HEAD'],where=peer).stdout.strip()==remote_head)
    (peer/'peer-only.txt').write_text('peer\n');git(['add','.'],where=peer);git(['commit','-m','Peer diverges'],where=peer)
    peer_head=git(['rev-parse','HEAD'],where=peer).stdout.strip()
    write('remote-only.txt','another-main\n');commit('Main diverges too');git(['push','origin','main']);git(['fetch','origin'],where=peer)
    refused=git(['merge','--ff-only','origin/main'],where=peer,success=False)
    check('ff_only_refuses_diverged_history',refused.returncode!=0 and git(['rev-parse','HEAD'],where=peer).stdout.strip()==peer_head)
    service=repo/'service';service.mkdir()
    source=Path(__file__).resolve().parent
    for name in FILES:(service/name).write_bytes((source/name).read_bytes())
    commit('Snapshot the actual teaching release sources')
    check('source_snapshot_matches_release_files',all(git(['rev-parse','HEAD:service/'+name]).stdout.strip()==git(['hash-object',str(source/name)]).stdout.strip() for name in FILES))
    git(['tag','fixture-v1']);tag=git(['rev-parse','fixture-v1']).stdout.strip()
    check('release_tag_identifies_a_commit',tag==git(['rev-parse','HEAD']).stdout.strip())
    observations={'staging':state,'merge_parents':parents,'rebase':{'before':old,'after':new,'new_parent':advance},
                  'revert':{'target':original,'inverse':reverted},'fetch':{'before_peer_head':old_peer,'remote_head':remote_head},
                  'release_revision':tag,'graph':git(['log','--all','--graph','--oneline','--decorate']).stdout}
    return {'checks':checks,'total':len(checks),'observations':observations,'commands':commands}

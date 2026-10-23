"""Private DRAFT-only intake for Studio Memory; no keys, approval, or Reader writes."""
import json
from pathlib import Path

from app import memory_workflow as workflow
from app.studio_memory import ID, _parse

REVIEWS = {'REVIEW_PASS', 'REVIEW_REWORK', 'REVIEW_HOLD'}


def initialize(root_path, vault_path):
    root = Path(root_path)
    vault = Path(vault_path).resolve(strict=True)
    if root.exists() or not vault.is_dir():
        raise ValueError('draft root exists or memory vault unavailable')
    root.mkdir(mode=0o700)
    for name in ('candidates', 'annotations', 'reviews'):
        (root / name).mkdir(mode=0o700)
    workflow._new_file(root / 'config.json', workflow._canonical({'version': 1, 'vault': str(vault)}))
    return root


def _root(path):
    root = workflow._private_root(path)
    workflow._config(root)
    return root


def _annotations(root, candidate):
    memory_id = candidate['id']
    data = json.loads(workflow._read_file(root / 'annotations' / (memory_id + '.json')))
    if (set(data) != {'project', 'unknowns', 'candidate_sha256'}
            or not isinstance(data['project'], str) or not 0 < len(data['project']) <= 120
            or not isinstance(data['unknowns'], list)
            or not all(isinstance(x, str) and 0 < len(x) <= 500 for x in data['unknowns'])
            or data['candidate_sha256'] != workflow._sha(workflow._canonical(candidate))):
        raise ValueError('invalid DRAFT annotations')
    return data


def add(root_path, report_path, fields, *, project='ZERO CODE', unknowns=None):
    root = _root(root_path)
    candidate = workflow.build_candidate(report_path, fields)
    memory_id = candidate['id']
    vault = workflow._config(root)
    if (vault / (memory_id + '.md')).exists() or (root / 'candidates' / (memory_id + '.json')).exists():
        raise ValueError('duplicate memory ID')
    unknowns = unknowns or []
    if not isinstance(project, str) or not 0 < len(project) <= 120:
        raise ValueError('invalid project')
    if not isinstance(unknowns, list) or not all(isinstance(x, str) and 0 < len(x) <= 500 for x in unknowns):
        raise ValueError('invalid unknowns')
    workflow._new_file(root / 'candidates' / (memory_id + '.json'), workflow._canonical(candidate))
    try:
        workflow._new_file(root / 'annotations' / (memory_id + '.json'),
                           workflow._canonical({'project': project, 'unknowns': unknowns,
                                                'candidate_sha256': workflow._sha(workflow._canonical(candidate))}))
    except Exception:
        (root / 'candidates' / (memory_id + '.json')).unlink()
        raise
    return candidate


def _source_state(candidate):
    try:
        source = workflow._read_file(candidate['source_path'])
        if workflow._sha(source) != candidate['source_sha256']:
            raise ValueError('source changed')
        text = source.decode('utf-8')
        for name in ('decision_excerpt', 'reason_excerpt'):
            if candidate[name] != workflow.UNKNOWN and candidate[name] not in text:
                raise ValueError('source excerpt missing')
        return 'MATCH'
    except (OSError, ValueError, UnicodeError):
        return 'MISMATCH_OR_MISSING'


def _reviews(root, memory_id):
    path = root / 'reviews' / (memory_id + '.jsonl')
    if not path.exists():
        return []
    return [json.loads(line) for line in workflow._read_file(path).splitlines() if line]


def _similar_drafts(root, candidate):
    matches = []
    for path in (root / 'candidates').glob('*.json'):
        if path.stem == candidate['id']:
            continue
        other = workflow._candidate(root, path.stem)
        _annotations(root, other)
        if (other['title'] == candidate['title'] or set(other['assets']) & set(candidate['assets'])
                or (set(other['characters']) & set(candidate['characters'])
                    and set(other['episodes']) & set(candidate['episodes']))):
            matches.append(other['id'])
    return sorted(matches)


def detail(root_path, memory_id):
    root = _root(root_path)
    candidate = workflow._candidate(root, memory_id)
    vault = workflow._config(root)
    related = []
    for related_id in candidate['related']:
        if not ID.fullmatch(related_id):
            raise ValueError('invalid related ID')
        path = vault / (related_id + '.md')
        if not path.is_file():
            related.append({'id': related_id, 'state': 'MISSING'})
        else:
            note = _parse(path)
            related.append({'id': related_id, 'title': note['title'],
                            'approval_status': note['approval_status'],
                            'approval_scope': note['approval_scope']})
    reviews = _reviews(root, memory_id)
    annotations = _annotations(root, candidate)
    return {'candidate': candidate, 'project': annotations['project'],
            'unknowns': annotations['unknowns'],
            'source_state': _source_state(candidate), 'related_memories': related,
            'existing_memory_overlap': workflow._conflicts(vault, candidate),
            'draft_overlap': _similar_drafts(root, candidate),
            'review_status': reviews[-1]['result'] if reviews else 'REVIEW_PENDING',
            'review_authority': 'ADVISORY_UNVERIFIED_LABEL',
            'review_history': reviews}


def list_candidates(root_path, *, proposed_by=None, character=None, asset=None, q=None):
    root = _root(root_path)
    if proposed_by is not None and proposed_by not in {'work01', 'work02'}:
        raise ValueError('invalid Work filter')
    if q is not None and (not isinstance(q, str) or len(q) > 120):
        raise ValueError('invalid query')
    output = []
    for path in sorted((root / 'candidates').glob('*.json')):
        candidate = workflow._candidate(root, path.stem)
        annotations = _annotations(root, candidate)
        if ((proposed_by is not None and candidate['proposed_by'] != proposed_by)
                or (character is not None and character not in candidate['characters'])
                or (asset is not None and asset not in candidate['assets'])
                or (q and q.casefold() not in ' '.join([candidate['id'], candidate['title'],
                    candidate['decision_excerpt'], *candidate['characters'], *candidate['assets']]).casefold())):
            continue
        reviews = _reviews(root, candidate['id'])
        output.append({'id': candidate['id'], 'title': candidate['title'],
                       'project': annotations['project'],
                       'proposed_by': candidate['proposed_by'], 'characters': candidate['characters'],
                       'assets': candidate['assets'], 'episodes': candidate['episodes'],
                       'workflow_status': 'DRAFT', 'approval_status': 'DRAFT',
                       'review_status': reviews[-1]['result'] if reviews else 'REVIEW_PENDING',
                       'review_authority': 'ADVISORY_UNVERIFIED_LABEL',
                       'source_state': _source_state(candidate), 'created_at': candidate['created_at']})
    return output


def review_packet(root_path, memory_id):
    data = detail(root_path, memory_id)
    candidate = data['candidate']
    return {'packet_type': 'AI_DIRECTOR_CONTENT_REVIEW_ONLY', 'formal_signature': False,
            'workflow_status': 'DRAFT', 'approval_status': 'DRAFT',
            'candidate_id': candidate['id'], 'title': candidate['title'],
            'project': data['project'], 'episodes': candidate['episodes'],
            'characters': candidate['characters'], 'assets': candidate['assets'],
            'decision_excerpt': candidate['decision_excerpt'],
            'reason_excerpt': candidate['reason_excerpt'],
            'source_path': candidate['source_path'], 'source_id': candidate['source_id'],
            'source_sha256': candidate['source_sha256'], 'source_state': data['source_state'],
            'candidate_sha256': workflow._sha(workflow._canonical(candidate)),
            'review_authority': 'ADVISORY_UNVERIFIED_LABEL',
            'approval_scope': candidate['approval_scope'],
            'related_memories': data['related_memories'],
            'existing_memory_overlap': data['existing_memory_overlap'],
            'draft_overlap': data['draft_overlap'],
            'unknowns': data['unknowns'] + candidate['unknown_fields'],
            'questions': ['出典と抜粋は現在も一致するか', '既存記憶と意味上の矛盾・重複があるか',
                          '承認範囲を超える読み方にならないか'],
            'possible_results': sorted(REVIEWS),
            'notice': 'AI内容レビューのみ。DIRECTOR_REVIEWED署名・正式登録ではない。'}


def record_review(root_path, memory_id, result, reviewer, note):
    root = _root(root_path)
    candidate = workflow._candidate(root, memory_id)
    _annotations(root, candidate)
    if result not in REVIEWS or not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError('invalid advisory review')
    if not isinstance(note, str) or not 0 < len(note) <= 2000:
        raise ValueError('review reason required')
    if result == 'REVIEW_PASS' and (_source_state(candidate) != 'MATCH' or candidate['unknown_fields']):
        raise ValueError('unverified candidate cannot pass content review')
    review = {'result': result, 'reviewer_label': reviewer, 'note': note,
              'candidate_sha256': workflow._sha(workflow._canonical(candidate)),
              'source_sha256': candidate['source_sha256'], 'at': workflow._now(),
              'advisory_only': True, 'review_authority': 'ADVISORY_UNVERIFIED_LABEL'}
    workflow._append_jsonl(root / 'reviews' / (memory_id + '.jsonl'), review)
    return review

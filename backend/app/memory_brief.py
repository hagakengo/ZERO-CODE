"""Read-only, scope-preserving production briefs from the existing Reader."""
from datetime import datetime, timezone
from urllib.parse import quote

REQUIRED = {'id', 'title', 'approval_status', 'approval_scope', 'sources', 'related',
            'updated_at', 'body'}


def _check_note(note):
    if not isinstance(note, dict) or not REQUIRED <= set(note):
        raise ValueError('incomplete memory detail')
    if (not isinstance(note['id'], str) or not isinstance(note['title'], str)
            or note['approval_status'] not in {'APPROVED', 'DRAFT', 'CANDIDATE', 'REWORK', 'UNVERIFIED'}
            or not isinstance(note['approval_scope'], str) or not isinstance(note['body'], str)
            or not isinstance(note['sources'], list) or not isinstance(note['related'], list)):
        raise ValueError('invalid memory detail')
    return note


def collect(fetch, query):
    """fetch(path) must return JSON from an authenticated Studio Memory Reader."""
    if not isinstance(query, str) or not query.strip() or len(query) > 120:
        raise ValueError('invalid brief query')
    path = '/api/studio/memory/search?q=' + quote(query, safe='')
    approved = fetch(path + '&approved_only=true')
    all_states = fetch(path)
    if (not isinstance(approved, dict) or not isinstance(all_states, dict)
            or not isinstance(approved.get('results'), list)
            or not isinstance(all_states.get('results'), list)
            or approved.get('approved_only') is not True
            or all_states.get('approved_only') is not False):
        raise ValueError('Reader search unavailable or access is approved-only')
    approved_ids = {item['id'] for item in approved['results']}
    all_ids = {item['id'] for item in all_states['results']}
    if len(all_ids) != len(all_states['results']) or len(approved_ids) != len(approved['results']):
        raise ValueError('duplicate Reader result')
    if not approved_ids <= all_ids:
        raise ValueError('Reader search scope mismatch')
    notes = []
    for item in all_states['results']:
        memory_id = item['id']
        detail = _check_note(fetch('/api/studio/memory/' + quote(memory_id, safe='')))
        for key in ('id', 'title', 'approval_status', 'approval_scope', 'sources', 'related', 'updated_at'):
            if detail[key] != item.get(key):
                raise ValueError('Reader search/detail mismatch')
        if (memory_id in approved_ids) != (detail['approval_status'] == 'APPROVED'):
            raise ValueError('Reader approval boundary mismatch')
        notes.append({key: detail[key] for key in
                      ('id', 'title', 'approval_status', 'approval_scope', 'sources', 'related', 'updated_at', 'body')})
    return sorted(notes, key=lambda x: x['id'])


def start_brief(target, query, notes):
    approved = [note for note in notes if note['approval_status'] == 'APPROVED']
    tentative = [note for note in notes if note['approval_status'] != 'APPROVED']
    return {'kind': 'PRODUCTION_START_BRIEF', 'target': target, 'query': query,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'reader_status': 'VERIFIED', 'approved_memories': approved,
            'unapproved_reference': tentative,
            'applicable_production_settings': [],
            'application_notice': '承認範囲を人が確認するまで、APPROVED記憶も本制作への適用済み設定とは扱わない。',
            'no_approved_memory_for_query': len(approved) == 0,
            'preflight_questions': ['対象制作に適用できる正式台帳・MASTERを別途確認したか',
                                    'DRAFTを正式設定と取り違えていないか',
                                    '未解決の演出・作画QCを制作前に確認したか']}


def review_brief(start, packet):
    if (not isinstance(start, dict) or start.get('kind') != 'PRODUCTION_START_BRIEF'
            or start.get('reader_status') != 'VERIFIED'
            or not isinstance(start.get('target'), str)
            or not isinstance(start.get('approved_memories'), list)
            or not isinstance(start.get('unapproved_reference'), list)):
        raise ValueError('unverified production start brief')
    for note in start['approved_memories'] + start['unapproved_reference']:
        _check_note(note)
    if (any(x['approval_status'] != 'APPROVED' for x in start['approved_memories'])
            or any(x['approval_status'] == 'APPROVED' for x in start['unapproved_reference'])):
        raise ValueError('production start approval boundary mismatch')
    if not isinstance(packet, dict) or any(packet.get(key) != value for key, value in
            {'packet_type': 'AI_DIRECTOR_CONTENT_REVIEW_ONLY', 'workflow_status': 'DRAFT',
             'approval_status': 'DRAFT', 'formal_signature': False, 'source_state': 'MATCH'}.items()):
        raise ValueError('unverified DRAFT review packet')
    if not isinstance(packet.get('candidate_id'), str) or not isinstance(packet.get('approval_scope'), str):
        raise ValueError('incomplete DRAFT review packet')
    qc = packet.get('os016_qc', {})
    return {'kind': 'DIRECTOR_REVIEW_BRIEF', 'target': start['target'],
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'candidate_id': packet['candidate_id'], 'candidate_status': 'DRAFT',
            'candidate_source_sha256': packet.get('source_sha256'),
            'candidate_source_state': packet['source_state'],
            'candidate_approval_scope': packet['approval_scope'],
            'candidate_related_ids': [item['id'] for item in packet.get('related_memories', [])],
            'technical_qc': qc.get('technical', 'UNVERIFIED'),
            'direction_and_drawing_qc': qc.get('direction_and_drawing', 'UNVERIFIED'),
            'master_approval': 'NOT_APPROVED', 'publication_approval': 'NOT_APPROVED',
            'formal_memory_registration': False, 'formal_director_signature': False,
            'advisory_recommendation': packet.get('os016_review_proposal', {}).get('recommended_result', 'UNVERIFIED'),
            'memory_evidence': [{'id': x['id'], 'status': x['approval_status'],
                                 'scope': x['approval_scope'], 'sources': x['sources'],
                                 'related': x['related']} for x in start['approved_memories'] + start['unapproved_reference']],
            'review_questions': ['過去のREWORK理由は再発していないか',
                                 'DRAFTの目元判断を正式デザインとして扱っていないか',
                                 'SNS公開範囲を本編MASTER承認に拡張していないか',
                                 '技術QCと演出・作画QCを分けて評価したか']}


def render_markdown(brief):
    lines = ['# ' + ('制作開始' if brief['kind'] == 'PRODUCTION_START_BRIEF' else '監督レビュー') + 'メモリーブリーフ',
             '', '対象：' + brief['target'], '状態：隔離検証用／正式承認台帳ではない', '']
    if brief['kind'] == 'PRODUCTION_START_BRIEF':
        lines += ['## 承認済み記憶', '']
        if not brief['approved_memories']:
            lines.append('検索で該当なし。制作への正式適用を確認済みの設定はない。')
        for note in brief['approved_memories']:
            lines += [f"- {note['id']}｜{note['title']}｜APPROVED（範囲：{note['approval_scope']}）",
                      '  出典：' + '、'.join(note['sources']) + '／関連：' + '、'.join(note['related'])]
        lines += ['', '## 未承認の参考判断', '']
        for note in brief['unapproved_reference']:
            lines += [f"- {note['id']}｜{note['title']}｜{note['approval_status']}（範囲：{note['approval_scope']}）",
                      '  出典：' + '、'.join(note['sources']) + '／関連：' + '、'.join(note['related']),
                      '  原文：' + note['body'].replace('\n', ' ')[:700]]
        if not brief['unapproved_reference']:
            lines.append('該当なし。')
        lines += ['', brief['application_notice'], '', '## 制作前の確認', '']
        lines += ['- ' + question for question in brief['preflight_questions']]
    else:
        lines += [f"候補：{brief['candidate_id']}｜DRAFT／出典：{brief['candidate_source_state']}",
                  f"技術QC：{brief['technical_qc']}／演出・作画QC：{brief['direction_and_drawing_qc']}",
                  '本編MASTER・公開・正式記憶登録：いずれも未承認',
                  f"内容レビュー提案：{brief['advisory_recommendation']}（未記録・未署名）", '',
                  '## 参照した記憶', '']
        for note in brief['memory_evidence']:
            lines.append(f"- {note['id']}｜{note['status']}｜範囲：{note['scope']}｜出典：{'、'.join(note['sources'])}")
        lines += ['', '## 監督の確認事項', '']
        lines += ['- ' + question for question in brief['review_questions']]
    return '\n'.join(lines) + '\n'

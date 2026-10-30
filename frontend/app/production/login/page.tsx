export default function Login() {
  return <main style={{ maxWidth: 420, margin: '12vh auto', padding: 24 }}><p>ZERO CODE STUDIO</p><h1 style={{ fontSize: 30 }}>制作室へログイン</h1><p style={{ color: '#a9b9c8', margin: '16px 0' }}>閲覧専用MVP。原画・レビュー・承認状態を安全に確認します。</p><form action="/api/studio/session" method="post" style={{ display: 'grid', gap: 20 }}>
    <label>ユーザー名<input name="username" required maxLength={128} autoComplete="username" style={{ display: 'block', width: '100%', padding: 12, background: '#16202c' }} /></label>
    <label>パスワード<input name="password" type="password" required maxLength={512} autoComplete="current-password" style={{ display: 'block', width: '100%', padding: 12, background: '#16202c' }} /></label>
    <button style={{ padding: 14, background: '#93ded0', color: '#06221c', borderRadius: 8 }}>制作状況を確認</button></form><p style={{ marginTop: 22 }}>入力を確認して再試行してください。認証情報が未設定の場合は管理担当へ確認してください。</p></main>;
}

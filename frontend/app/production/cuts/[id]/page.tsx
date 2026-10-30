import StudioView from '../../StudioView';
export default async function Page({ params }: { params: Promise<{ id: string }> }) { const { id } = await params; return <StudioView view="cut" cutId={id} />; }

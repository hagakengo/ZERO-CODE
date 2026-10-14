import bpy,json,pathlib
p=pathlib.Path(__file__).resolve().parent
s=bpy.context.scene
gp=[o for o in bpy.data.objects if o.type=='GREASEPENCIL']
r={'blender':bpy.app.version_string,'fps':s.render.fps,'frame_start':s.frame_start,'frame_end':s.frame_end,'gp':[{'name':o.name,'layers':[{'name':l.name,'drawings':len(l.frames)} for l in o.data.layers]} for o in gp]}
assert gp and s.frame_end==72 and s.render.fps==24
assert sum(len(l.frames) for o in gp for l in o.data.layers)==72
(p/'native_reopen_qa.json').write_text(json.dumps(r,indent=2)+'\n')
s.frame_set(36);s.render.filepath=str(p/'reopened_frame_0036.png');bpy.ops.render.render(write_still=True)

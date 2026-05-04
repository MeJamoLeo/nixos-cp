function renderHUD(d) {
	const h = d.hud || {}, ps = d.player_status || {};
	const fc = (d.contests||[])[0];
	function s(l,v,sub,c) {
		return '<div class="hud-section"><div class="hud-label">'+l+'</div><div class="hud-value" style="color:'+c+'">'+v+'</div>'+(sub?'<div class="hud-sub">'+sub+'</div>':'')+'</div>';
	}
	const todayAc = (ps.today_acs||[]).length;
	const totalAc = h.ac_count || 0;

	// Next color band calculation using RPS efficiency
	const colorBands=[[400,'茶','#804000'],[800,'緑','#008000'],[1200,'水','#00c0c0'],[1600,'青','#0000ff'],[2000,'黄','#c0c000'],[2400,'橙','#ff8000'],[2800,'赤','#ff0000']];
	const curRating=ps.rating||0;
	let nextLabel='?',nextColor='#4a6a4a',targetR=400;
	for(let i=0;i<colorBands.length;i++){if(curRating<colorBands[i][0]){nextLabel=colorBands[i][1];nextColor=colorBands[i][2];targetR=colorBands[i][0];break;}}
	const remain=targetR-curRating;
	const dl=d.difficulty_log||{};
	const avgWkDiff=dl.avg_weekly_diff||0;
	const eff=dl.rps_efficiency||0.005;
	let nextEstimate='';
	if(avgWkDiff>0){
		const wkGain=avgWkDiff*eff;
		const weeks=Math.ceil(remain/wkGain);
		nextEstimate=weeks<=4?weeks+'週':Math.ceil(weeks/4)+'ヶ月';
		nextEstimate+=' (週'+avgWkDiff+'diff)';
	}else{
		nextEstimate='精進再開待ち';
	}

	return '<div class="hud" style="background:var(--dbg-hud)">'
		+s('user',(d.user||'---'),'','#1a5a2a')
		+s('rating',h.rating+' <span style="color:var(--dim)">'+(h.rank_label||'')+'</span>','','var(--amber)')
		+s('streak','🔥 '+(h.streak_days||0)+'日','','#ff8030')
		+s('today ac',todayAc+'問','total '+(totalAc),'var(--green)')
		+s('合計AC',totalAc+'問','','var(--cyan)')
		+s('初AC',h.first_ac_today||'--:--','avg '+(h.avg_first_ac||'--:--'),'#ffcc00')
		+s(nextLabel+'まで','+'+remain,nextEstimate,nextColor)
		+(fc?'<div class="hud-boss"><div><div style="font-size:var(--fs-2xs);color:#3a2a00;letter-spacing:.12em;text-transform:uppercase">BOSS FIGHT</div><div style="font-size:var(--fs-md);color:var(--amber);font-weight:500" id="boss-name">'+fc.type+' '+fc.id.replace(/[a-z]+/,'')+'</div></div><div class="hud-boss-timer" id="boss-timer">--:--:--</div></div>':'')
		+'</div>';
}

function renderPlayerStatus(d) {
	const ps = d.player_status||{}, h = d.hud||{};
	const pct = ((ps.rating_progress||0)*100).toFixed(1);
	const todayAc = (ps.today_acs||[]).length;
	const totalAc = h.ac_count || 0;
	return '<div class="panel accent-amber" data-label="PLAYER STATUS" style="background:var(--dbg-player)"><div class="panel-inner">'
		+'<div style="display:flex;justify-content:space-between;align-items:flex-end"><div><div style="font-size:var(--fs-sm);color:#8aaa9a">RATING</div><div class="ps-rating">'+(ps.rating||0)+'</div></div><div style="text-align:right"><div style="font-size:var(--fs-sm);color:#8aaa9a">AC</div><div class="ps-level">'+totalAc+'</div></div></div>'
		+'<div class="progress-bar"><div class="progress-fill" style="width:'+pct+'%;background:var(--amber)"></div></div>'
		+'<div style="display:flex;justify-content:space-between;font-size:var(--fs-sm);color:var(--muted)"><span>'+(ps.rating_min||0)+'</span><span style="color:var(--amber)">'+(ps.rating||0)+'</span><span style="color:var(--green)">'+(ps.rating_max||0)+'</span></div>'
		+'<div class="ps-box-green"><div style="font-size:var(--fs-sm);color:#3a8a5a">TODAY AC</div><div><span class="ps-xp">'+todayAc+'</span> <span style="font-size:var(--fs-sm);color:#1a5a1a">問</span></div></div>'
		+'<div class="ps-box-amber"><span style="font-size:var(--fs-lg)">🔥</span><div><span class="ps-streak">'+(ps.streak_days||0)+'</span> <span style="font-size:var(--fs-sm);color:#6a3a00">日連続</span><div style="font-size:var(--fs-sm);color:#5a3a00">最長: '+(ps.max_streak||0)+'日</div></div></div>'
		+'</div></div>';
}

function renderContestList(d) {
	const days=['日','月','火','水','木','金','土'];
	let h='<div class="section-label">コンテスト</div>';
	(d.contests||[]).slice(0,5).forEach((c,i)=>{const dt=new Date(c.start_epoch*1000),ds=(dt.getMonth()+1)+'/'+dt.getDate()+' ('+days[dt.getDay()]+') '+String(dt.getHours()).padStart(2,'0')+':'+String(dt.getMinutes()).padStart(2,'0'),b=c.type==='ABC'?'contest-badge-abc':c.type==='ARC'?'contest-badge-arc':'contest-badge-ahc',r=c.is_rated_for_user?'<div class="contest-rated yes">'+c.rated_range+' ●</div>':'<div class="contest-rated">対象外</div>',t=c.title.replace(/.*\(/,'').replace(/\)$/,'').replace('AtCoder ','');
	h+='<div class="contest-item"><span class="contest-badge '+b+'">'+c.type+'</span><div style="flex:1;min-width:0"><div class="contest-name">'+t+'</div><div class="contest-time"'+(i===0?' style="color:var(--amber)"':'')+'>'+ds+(i===0?' BOSS':'')+'</div></div>'+r+'</div>';});
	return h;
}

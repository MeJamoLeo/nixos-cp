function renderHUD(d) {
	const h = d.hud || {}, ps = d.player_status || {}, sp = d.speed || [];
	const last = sp.length ? sp[sp.length-1] : null;
	const spd = last ? Math.floor(last.avg_a_seconds/60)+':'+String(last.avg_a_seconds%60).padStart(2,'0') : '--';
	const fc = (d.contests||[])[0];
	function s(l,v,sub,c) {
		return '<div class="hud-section"><div class="hud-label">'+l+'</div><div class="hud-value" style="color:'+c+'">'+v+'</div>'+(sub?'<div class="hud-sub">'+sub+'</div>':'')+'</div>';
	}
	const todayAc = (ps.today_acs||[]).length;
	const totalAc = h.ac_count || 0;
	const cmp = d.compare || {};
	const monthAc = cmp.this_month_ac || 0;

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
		+s('月AC',monthAc+'問','','var(--blue)')
		+s('合計AC',totalAc+'問','','var(--cyan)')
		+s('早朝AC',h.first_ac_today||'--:--','avg '+(h.avg_first_ac||'--:--'),'#ffcc00')
		+s(nextLabel+'まで','+'+remain,nextEstimate,nextColor)
		+''
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

function renderWAQueue(d) {
	const wq = d.wa_queue||[];
	let items = '';
	wq.forEach(w => {
		const c = w.wa_count>=3?'#cc4444':w.wa_count>=2?'var(--amber)':'#333';
		items += '<div class="wa-item"><div class="wa-indicator" style="background:'+c+'"></div><span class="wa-badge">×'+w.wa_count+'</span><span class="wa-name">'+w.problem_id+'</span><span class="wa-tag">'+w.tag+'</span><span class="wa-diff">'+w.difficulty+'</span></div>';
	});
	return '<div class="panel" data-label="WA QUEUE" style="flex:1;background:var(--dbg-waqueue)"><div class="panel-inner"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px"><span style="font-size:var(--fs-xs);color:var(--dim)">復習待ち '+wq.length+'問</span><span class="badge badge-amber">優先順</span></div>'+items+'</div></div>';
}

function renderLanguageStats(d) {
	const ls=d.language_stats||[];
	if(!ls.length)return '<div class="section-label">言語別AC</div>';
	const max=ls[0].count;
	let h='<div class="section-label">言語別AC</div>';
	ls.forEach((l,i)=>{const pct=Math.round(l.count/max*100);const c=i===0?'var(--cyan)':i<3?'var(--green)':'var(--dim)';h+='<div class="tag-row'+(i===0?' active':'')+'"><span class="tag-name">'+l.lang+'</span><div class="tag-bar"><div class="tag-bar-fill" style="width:'+pct+'%;background:'+c+'"></div></div><span class="tag-pct" style="color:'+c+'">'+l.count+'</span></div>';});
	return h;
}

function renderPeerTable(d) {
	let h='<div class="section-label">同レート帯 ±50</div><div class="peer-row" style="font-size:var(--fs-2xs);color:var(--muted)"><span>user</span><span class="peer-num">rate</span><span class="peer-num">月AC</span></div>';
	(d.peers||[]).forEach(p=>{const s=p.is_self,n=s?'← '+p.user:p.user;h+='<div class="peer-row'+(s?' peer-self':'')+'"><span style="color:'+(s?'var(--green)':'#5a7a7a')+'">'+n+'</span><span class="peer-num" style="color:'+(s?'var(--amber)':'#4a4a4a')+'">'+p.rating+'</span><span class="peer-num">'+p.monthly_ac+'</span></div>';});
	return h;
}

function renderQualityBar(d) {
	const q=d.quality||{};
	return '<div style="font-size:var(--fs-2xs);color:var(--muted);margin-bottom:2px">解答の質</div>'
		+'<div class="quality-bar"><div class="quality-seg" style="width:'+(q.first_sight||0)+'%;background:var(--green)"></div><div class="quality-seg" style="width:'+(q.self_solve||0)+'%;background:#2a6a4a"></div><div class="quality-seg" style="width:'+(q.impl_fail||0)+'%;background:var(--amber)"></div><div class="quality-seg" style="width:'+(q.editorial||0)+'%;background:#4a2a1a"></div></div>'
		+'<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px;margin-top:2px;font-size:var(--fs-2xs);color:var(--dim)"><span>● 初見 '+(q.first_sight||0)+'%</span><span>● 自力 '+(q.self_solve||0)+'%</span><span>● 実装× '+(q.impl_fail||0)+'%</span><span>● 解説 '+(q.editorial||0)+'%</span></div>';
}

function renderSpeedBars(d) {
	const sp=d.speed||[];
	if(!sp.length)return '';
	function fmt(s){const m=Math.floor(s/60),sec=String(s%60).padStart(2,'0');return m+':'+sec;}
	let h='<div class="section-label">ラップタイム</div>';
	sp.slice(-8).forEach(c=>{
		const dur=c.duration_seconds||(c.contest.includes('ARC')?7200:6000);
		const totalUsed=c.laps.length?c.laps[c.laps.length-1].cumulative:0;
		const remaining=Math.max(dur-totalUsed,0);
		h+='<div style="margin-bottom:3px"><div style="font-size:var(--fs-xs);color:var(--dim);margin-bottom:1px">'+c.contest+' <span style="color:var(--muted)">'+fmt(dur)+'</span></div>';
		h+='<div style="display:flex;height:16px;background:var(--bar-bg)">';
		c.laps.forEach(l=>{
			const col=l.problem==='A'?'#335577':l.problem==='B'?'#3a7a5a':l.problem==='C'?'var(--amber)':l.problem==='D'?'var(--cyan)':'var(--green)';
			const pct=(l.lap/dur*100).toFixed(1);
			h+='<div style="width:'+pct+'%;background:'+col+';display:flex;align-items:center;justify-content:center;font-size:var(--fs-2xs);overflow:hidden;white-space:nowrap">'+l.problem+' '+fmt(l.lap)+'</div>';
		});
		if(remaining>0){
			const pct=(remaining/dur*100).toFixed(1);
			h+='<div style="width:'+pct+'%;display:flex;align-items:center;justify-content:center;font-size:var(--fs-2xs);color:var(--muted);overflow:hidden"></div>';
		}
		h+='</div>';
		h+='<div style="display:flex;gap:4px;font-size:var(--fs-2xs);color:var(--dim);margin-top:1px">';
		c.laps.forEach(l=>{
			const col=l.problem==='A'?'#335577':l.problem==='B'?'#3a7a5a':l.problem==='C'?'var(--amber)':l.problem==='D'?'var(--cyan)':'var(--green)';
			h+='<span style="color:'+col+'">'+l.problem+':'+fmt(l.lap)+'</span>';
		});
		h+='</div></div>';
	});
	return h;
}

function renderContestList(d) {
	const days=['日','月','火','水','木','金','土'];
	let h='<div class="section-label">コンテスト</div>';
	(d.contests||[]).slice(0,5).forEach((c,i)=>{const dt=new Date(c.start_epoch*1000),ds=(dt.getMonth()+1)+'/'+dt.getDate()+' ('+days[dt.getDay()]+') '+String(dt.getHours()).padStart(2,'0')+':'+String(dt.getMinutes()).padStart(2,'0'),b=c.type==='ABC'?'contest-badge-abc':c.type==='ARC'?'contest-badge-arc':'contest-badge-ahc',r=c.is_rated_for_user?'<div class="contest-rated yes">'+c.rated_range+' ●</div>':'<div class="contest-rated">対象外</div>',t=c.title.replace(/.*\(/,'').replace(/\)$/,'').replace('AtCoder ','');
	h+='<div class="contest-item"><span class="contest-badge '+b+'">'+c.type+'</span><div style="flex:1;min-width:0"><div class="contest-name">'+t+'</div><div class="contest-time"'+(i===0?' style="color:var(--amber)"':'')+'>'+ds+(i===0?' BOSS':'')+'</div></div>'+r+'</div>';});
	return h;
}

function renderRecommend(d) {
	const rec = d.recommend || [];
	let h = '<div class="section-label">おすすめ問題</div>';
	if (!rec.length) {
		h += '<div style="font-size:var(--fs-sm);color:var(--dim);padding:4px 0">データ取得中...</div>';
		return h;
	}
	rec.forEach(r => {
		const url = r.url || '#';
		h += '<div class="wa-item">'
			+ '<div class="wa-indicator" style="background:var(--cyan)"></div>'
			+ '<a href="'+url+'" style="font-size:var(--fs-md);color:var(--cyan);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;text-decoration:none">'+r.problem_id+'</a>'
			+ '<span class="wa-tag">'+r.tag+'</span>'
			+ '<span class="wa-diff">'+r.difficulty+'</span></div>';
	});
	return h;
}

function renderCompare(d) {
	const cmp = d.compare || {};
	const rh = d.rating_history || [];
	let h = '<div class="section-label">成長比較 + 直近コンテスト</div>';

	h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-bottom:4px">';
	h += '<div style="font-size:var(--fs-xs);color:var(--dim);text-align:center;padding:2px;background:#040c04;border:0.5px solid #0a2a0a">'
		+ '<div>先月</div><div style="font-size:var(--fs-lg);color:var(--green)">'+(cmp.last_month_ac||0)+'<span style="font-size:var(--fs-xs)"> AC</span></div></div>';
	h += '<div style="font-size:var(--fs-xs);color:var(--dim);text-align:center;padding:2px;background:#040c04;border:0.5px solid #0a2a0a">'
		+ '<div>今月</div><div style="font-size:var(--fs-lg);color:var(--cyan)">'+(cmp.this_month_ac||0)+'<span style="font-size:var(--fs-xs)"> AC</span></div></div>';
	h += '</div>';

	const sp = d.speed || [];
	const recent = rh.slice(-20).reverse();
	if (recent.length) {
		h += '<div class="section-label" style="margin-top:4px">直近コンテスト</div>';
		recent.forEach(r => {
			const delta = r.new_rating - r.old_rating;
			const color = delta >= 0 ? 'var(--green)' : 'var(--red)';
			const sign = delta >= 0 ? '+' : '';
			const name = (r.contest||'').replace(/AtCoder /,'').replace(/Beginner Contest /,'ABC').replace(/Regular Contest /,'ARC').substring(0,18);
			const perfCol = ratingColor(r.performance);
			h += '<div style="display:flex;align-items:center;gap:3px;padding:1px 0;border-bottom:0.5px solid var(--border);font-size:var(--fs-2xs)">';
			h += '<span style="color:var(--dim);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+name+'</span>';
			h += '<span style="color:'+perfCol+';min-width:28px;text-align:right">'+r.performance+'</span>';
			h += '<span style="color:'+color+';min-width:28px;text-align:right;font-weight:500">'+sign+delta+'</span>';
			h += '</div>';
		});
	}
	return h;
}

function renderInsight(d) {
	let h = '';
	if (d.insight) {
		h += '<div class="insight-box" style="background:var(--dbg-insight)">'
			+ '<div style="display:flex;justify-content:space-between;font-size:var(--fs-sm);color:#3a8a5a">'
			+ '<span>最近の洞察</span><span style="color:#2a6a4a">'+(d.insight.tag||'')+' · diff'+(d.insight.difficulty||'')+'</span></div>'
			+ '<div class="insight-text">'+d.insight.text+'</div></div>';
	}
	return h;
}

function renderAchievements(d) {
	if (!d.achievements) return '';
	const a = d.achievements;
	let h = '<div class="achievement-bar" style="height:100%;background:var(--dbg-achieve)">'
		+ '<span style="font-size:var(--fs-2xs);color:var(--muted);white-space:nowrap">実績 '+a.unlocked+'/'+a.total+'</span>'
		+ '<div class="achievement-grid">';
	(a.list||[]).forEach(m => {
		const c = m.status==='gold'?' gold':m.status==='new'?' fresh':m.status==='lock'?' locked':'';
		h += '<div class="achievement-item'+c+'"><div class="achievement-icon">'+m.icon+'</div><div class="achievement-label">'+m.label+'</div></div>';
	});
	h += '</div></div>';
	return h;
}

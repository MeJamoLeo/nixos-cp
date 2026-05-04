function hydrate() {
	const d = window.__CP_DATA;
	if (!d) return;
	const vp = window.__VP || {w:1080, h:675};
	document.body.innerHTML = renderHUD(d)
		+'<div class="main">'
		+'<div class="col-left">'
			+'<div style="flex:1;display:flex;flex-direction:column;min-height:0;overflow:hidden">'+renderPlayerStatus(d)+'</div>'
			+'<div class="panel" style="flex:1;min-height:0"></div>'
			+'<div class="panel" style="flex:1;min-height:0"></div>'
			+'<div class="panel" style="flex:1;min-height:0"></div>'
		+'</div>'
		+'<div class="col-right">'
			+'<div class="col-right-top">'
				+renderDifficultyLog(d)
				+'<div class="panel" data-label="SKILL GRAPH" style="overflow:hidden;background:var(--dbg-skillgraph)"><div class="panel-inner" style="display:flex;flex:1;min-height:0">'+renderSkillGraph(d)+'</div></div>'
			+'</div>'
			+'<div class="col-right-bottom">'
				+'<div class="panel"></div>'
				+'<div class="panel"></div>'
				+'<div class="panel accent-amber" data-label="STREAK" style="background:var(--dbg-streak)"><div class="panel-inner">'+renderStreakCalendar(d)+'</div></div>'
				+'<div class="panel"></div>'
				+'<div class="panel accent-cyan" data-label="CONTEST" style="background:var(--dbg-speed)"><div class="panel-inner">'+renderContestList(d)+'</div></div>'
			+'</div>'
		+'</div>'
		+'</div>';

	const fc=(d.contests||[])[0];
	if(fc){const bt=document.getElementById('boss-timer');if(bt)setInterval(()=>{const diff=fc.start_epoch-Date.now()/1000;if(diff<=0){bt.textContent='LIVE';return;}bt.textContent=Math.floor(diff/3600)+':'+String(Math.floor((diff%3600)/60)).padStart(2,'0')+':'+String(Math.floor(diff%60)).padStart(2,'0');},1000);}
}

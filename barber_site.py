#!/usr/bin/env python3
"""
The Barber - booking site + private portal.
A small self-contained web app: no external libraries, stores data in a local
SQLite file (barber.db). Run:  python3 server.py   then open http://localhost:8000
"""
import http.server
import socketserver
import sqlite3
import json
import os
import secrets
from datetime import date, datetime, timedelta
from urllib.parse import urlparse, parse_qs


# ===== embedded website files (everything in ONE file) =====
STYLE_CSS = r"""
:root {
  --bg: #ffffff;
  --ink: #1a1a1a;
  --muted: #6b7280;
  --line: #ececec;
  --soft: #f7f7f8;
  --accent: #1a1a1a;
  --accent-ink: #ffffff;
  --ok: #1f9d55;
  --okbg: #e9f7ef;
  --warn: #9a6400;
  --warnbg: #fff4e5;
  --err: #c0392b;
  --errbg: #fdecea;
  --radius: 14px;
  --shadow: 0 1px 2px rgba(0,0,0,.04), 0 8px 24px rgba(0,0,0,.05);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--ink);
  background: #eef0f3;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

.stage { min-height: 100%; display: flex; justify-content: center; align-items: flex-start; padding: 32px 16px 60px; }
.device { width: 100%; max-width: 440px; background: var(--bg); border-radius: 28px; box-shadow: var(--shadow); overflow: hidden; position: relative; min-height: 720px; }

.screen { display: none; padding: 28px 24px 40px; }
.screen.active { display: block; animation: fade .25s ease; }
@keyframes fade { from { opacity: 0; transform: translateY(6px);} to {opacity:1; transform:none;} }

h1 { font-size: 26px; font-weight: 700; letter-spacing: -0.02em; }
h2 { font-size: 19px; font-weight: 700; letter-spacing: -0.01em; }
.brand { font-size: 14px; letter-spacing: .18em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
.sub { color: var(--muted); font-size: 15px; margin-top: 4px; }
.label { font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); font-weight: 700; margin: 26px 0 12px; }

.hero { text-align: center; padding: 18px 0 8px; }
.logo-dot { width: 64px; height: 64px; border-radius: 50%; background: var(--ink); color: #fff; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; font-size: 26px; font-weight: 700; }

.card { border: 1.5px solid var(--line); border-radius: var(--radius); padding: 16px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; transition: border-color .15s, background .15s; margin-bottom: 10px; }
.card:hover { border-color: #d6d6d6; }
.card.selected { border-color: var(--ink); background: var(--soft); }
.card .meta { display: flex; flex-direction: column; }
.card .name { font-weight: 600; font-size: 16px; }
.card .dur { color: var(--muted); font-size: 13px; margin-top: 2px; }
.card .price { font-weight: 700; font-size: 16px; }

.cal { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }
.day { flex: 0 0 auto; width: 56px; text-align: center; padding: 10px 0; border-radius: 12px; border: 1.5px solid var(--line); cursor: pointer; transition: .15s; }
.day:hover { border-color: #d6d6d6; }
.day.selected { background: var(--ink); color: #fff; border-color: var(--ink); }
.day .dow { font-size: 11px; text-transform: uppercase; letter-spacing: .08em; opacity: .7; }
.day .num { font-size: 18px; font-weight: 700; margin-top: 2px; }

.slots { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.slot { text-align: center; padding: 11px 0; border: 1.5px solid var(--line); border-radius: 10px; cursor: pointer; font-weight: 600; font-size: 14px; transition: .15s; }
.slot:hover { border-color: #d6d6d6; }
.slot.selected { background: var(--ink); color: #fff; border-color: var(--ink); }
.slot.taken { color: #c9c9c9; cursor: not-allowed; text-decoration: line-through; background: var(--soft); }
.slots .empty { grid-column: 1 / -1; color: var(--muted); font-size: 14px; padding: 6px 0; }

.field { margin-bottom: 12px; }
input, textarea { width: 100%; border: 1.5px solid var(--line); border-radius: 10px; padding: 13px 14px; font-size: 15px; font-family: inherit; color: var(--ink); background: #fff; }
input:focus, textarea:focus { outline: none; border-color: var(--ink); }
textarea { resize: vertical; min-height: 72px; }

.btn { display: block; width: 100%; text-align: center; padding: 15px; border-radius: 12px; background: var(--accent); color: var(--accent-ink); font-size: 16px; font-weight: 600; border: none; cursor: pointer; margin-top: 22px; transition: opacity .15s; }
.btn:hover { opacity: .9; }
.btn.ghost { background: #fff; color: var(--ink); border: 1.5px solid var(--line); }
.btn:disabled { opacity: .4; cursor: not-allowed; }

.confirm-mark { width: 76px; height: 76px; border-radius: 50%; background: var(--okbg); color: var(--ok); display: flex; align-items: center; justify-content: center; font-size: 40px; margin: 30px auto 20px; }
.recap { background: var(--soft); border-radius: var(--radius); padding: 18px; margin-top: 22px; }
.recap .row { display: flex; justify-content: space-between; padding: 7px 0; }
.recap .row .k { color: var(--muted); }
.recap .row .v { font-weight: 600; }
.reminder-note { display: flex; gap: 10px; align-items: flex-start; background: var(--okbg); color: #126b3a; border-radius: 12px; padding: 13px 14px; margin-top: 18px; font-size: 14px; }

.topbar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.daynav { display: flex; align-items: center; gap: 14px; margin: 18px 0 6px; }
.daynav .arrow { width: 34px; height: 34px; border-radius: 9px; border: 1.5px solid var(--line); display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 16px; user-select: none; }
.daynav .arrow:hover { border-color: #d6d6d6; }
.daynav .today { font-weight: 700; font-size: 16px; }
.countline { color: var(--muted); font-size: 14px; margin: 10px 0 18px; }

.appt { display: flex; align-items: center; gap: 14px; padding: 14px; border: 1.5px solid var(--line); border-radius: 12px; margin-bottom: 10px; cursor: pointer; transition: .15s; }
.appt:hover { border-color: #cfcfcf; box-shadow: var(--shadow); }
.appt .time { font-weight: 700; font-size: 15px; width: 64px; flex: 0 0 auto; }
.appt .who { flex: 1; }
.appt .who .nm { font-weight: 600; }
.appt .who .svc { color: var(--muted); font-size: 13px; margin-top: 2px; }
.appt .chev { color: #c4c4c4; font-size: 18px; }

.pill { font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 999px; display: inline-flex; gap: 4px; align-items: center; white-space: nowrap; }
.pill.sent { background: var(--okbg); color: #126b3a; }
.pill.sched { background: var(--warnbg); color: var(--warn); }

.open-slot { display: flex; align-items: center; gap: 14px; padding: 12px 14px; border: 1.5px dashed #e2e2e2; border-radius: 12px; margin-bottom: 10px; color: #b8b8b8; font-size: 14px; }
.open-slot .time { font-weight: 700; width: 64px; flex: 0 0 auto; }

.backbar { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.back { width: 36px; height: 36px; border-radius: 10px; border: 1.5px solid var(--line); display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 18px; user-select: none; }
.back:hover { border-color: #d6d6d6; }

.client-head { display: flex; align-items: center; gap: 14px; }
.avatar { width: 56px; height: 56px; border-radius: 50%; background: var(--soft); color: var(--ink); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 20px; flex: 0 0 auto; }
.contact-row { display: flex; gap: 10px; margin-top: 16px; }
.contact-row a { flex: 1; text-align: center; text-decoration: none; color: var(--ink); font-weight: 600; font-size: 14px; border: 1.5px solid var(--line); border-radius: 11px; padding: 11px; transition: .15s; }
.contact-row a:hover { border-color: #cfcfcf; background: var(--soft); }

.panel { background: var(--soft); border-radius: var(--radius); padding: 16px; margin-top: 14px; }
.panel .row { display: flex; justify-content: space-between; padding: 5px 0; }
.panel .row .k { color: var(--muted); }
.panel .row .v { font-weight: 600; text-align: right; }
.request { font-style: italic; color: #374151; margin-top: 8px; background:#fff; border-radius:10px; padding:10px 12px; border:1px solid var(--line); }

.notes-row { display:flex; align-items:center; justify-content:space-between; }
.save-note { font-size: 13px; font-weight: 700; color: var(--ink); background: none; border: none; cursor: pointer; padding: 0; }
.save-note.saved { color: var(--ok); }
.visit { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--line); }
.visit:last-child { border-bottom: none; }
.visit .d { font-weight: 600; }
.visit .s { color: var(--muted); font-size: 14px; }

.hint { text-align:center; color:#9aa0a6; font-size:12px; margin-top:14px; }
.msg { border-radius: 10px; padding: 11px 14px; font-size: 14px; margin-top: 14px; display:none; }
.msg.show { display:block; }
.msg.error { background: var(--errbg); color: var(--err); }
.icon { width: 1em; height: 1em; vertical-align: -0.125em; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
"""

BOOKING_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>The Barber — Book an Appointment</title>
<link rel="stylesheet" href="/style.css" />
</head>
<body>
<div class="stage">
  <div class="device">

    <!-- BOOKING -->
    <section id="screen-booking" class="screen active">
      <div class="hero">
        <div class="logo-dot">B</div>
        <div class="brand">The Barber</div>
        <h1 style="margin-top:6px;">Book your next cut</h1>
        <p class="sub">Pick a service, choose a time, you're done.</p>
      </div>

      <div class="label">Step 1 · Choose a service</div>
      <div id="services"></div>

      <div class="label">Step 2 · Pick a day</div>
      <div class="cal" id="cal"></div>

      <div class="label">Step 3 · Pick a time</div>
      <div class="slots" id="slots"></div>

      <div class="label">Step 4 · Your details</div>
      <div class="field"><input id="f-name" type="text" placeholder="Full name" /></div>
      <div class="field"><input id="f-phone" type="tel" placeholder="Phone number" /></div>
      <div class="field"><input id="f-email" type="email" placeholder="Email" /></div>
      <div class="field"><textarea id="f-request" placeholder="Anything I should know? (optional)"></textarea></div>

      <div id="book-msg" class="msg error"></div>
      <button id="book-btn" class="btn" onclick="book()">Book Appointment</button>
    </section>

    <!-- CONFIRMATION -->
    <section id="screen-confirm" class="screen">
      <div class="confirm-mark">✓</div>
      <h1 style="text-align:center;">You're all set!</h1>
      <p class="sub" style="text-align:center;">See you soon. A confirmation is on its way.</p>
      <div class="recap">
        <div class="row"><span class="k">Service</span><span class="v" id="r-svc">—</span></div>
        <div class="row"><span class="k">Date</span><span class="v" id="r-date">—</span></div>
        <div class="row"><span class="k">Time</span><span class="v" id="r-time">—</span></div>
        <div class="row"><span class="k">With</span><span class="v">The Barber</span></div>
      </div>
      <div class="reminder-note">
        <svg class="icon" viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/></svg>
        <span>We'll remind you by <b>text and email</b> the day before your appointment.</span>
      </div>
      <button class="btn ghost" onclick="alert('This would add the appointment to your phone calendar.')">＋ Add to Calendar</button>
      <button class="btn" onclick="resetBooking()">Book another</button>
    </section>

  </div>
</div>

<script>
  var state = { service: null, price: null, date: null, time: null };

  function api(path, opts) {
    return fetch(path, opts).then(function(r){ return r.json().then(function(j){ return {ok:r.ok, body:j}; }); });
  }
  function go(name) {
    document.querySelectorAll('.screen').forEach(function(s){ s.classList.remove('active'); });
    document.getElementById('screen-'+name).classList.add('active');
    window.scrollTo(0,0);
  }

  // Step 1: services
  function loadServices() {
    api('/api/services').then(function(res){
      var el = document.getElementById('services'); el.innerHTML = '';
      res.body.services.forEach(function(s, i){
        var div = document.createElement('div');
        div.className = 'card' + (i===0 ? ' selected' : '');
        div.innerHTML = '<div class="meta"><span class="name">'+s.name+'</span><span class="dur">'+s.minutes+' min</span></div><span class="price">$'+s.price+'</span>';
        div.onclick = function(){
          document.querySelectorAll('#services .card').forEach(function(c){ c.classList.remove('selected'); });
          div.classList.add('selected');
          state.service = s.name; state.price = s.price;
        };
        el.appendChild(div);
        if (i===0) { state.service = s.name; state.price = s.price; }
      });
    });
  }

  // Step 2: days
  function loadDays() {
    api('/api/days').then(function(res){
      var el = document.getElementById('cal'); el.innerHTML = '';
      res.body.days.forEach(function(d, i){
        var div = document.createElement('div');
        div.className = 'day' + (i===0 ? ' selected' : '');
        div.innerHTML = '<div class="dow">'+d.dow+'</div><div class="num">'+d.num+'</div>';
        div.onclick = function(){
          document.querySelectorAll('#cal .day').forEach(function(c){ c.classList.remove('selected'); });
          div.classList.add('selected');
          state.date = d.date; state.time = null;
          loadSlots();
        };
        el.appendChild(div);
        if (i===0) state.date = d.date;
      });
      loadSlots();
    });
  }

  // Step 3: time slots for the chosen day
  function loadSlots() {
    api('/api/slots?date='+encodeURIComponent(state.date)).then(function(res){
      var el = document.getElementById('slots'); el.innerHTML = '';
      var anyFree = false;
      res.body.slots.forEach(function(s){
        var div = document.createElement('div');
        div.className = 'slot' + (s.taken ? ' taken' : '');
        div.textContent = s.label;
        if (!s.taken) {
          anyFree = true;
          div.onclick = function(){
            document.querySelectorAll('#slots .slot').forEach(function(c){ c.classList.remove('selected'); });
            div.classList.add('selected');
            state.time = s.time;
          };
        }
        el.appendChild(div);
      });
      if (!anyFree) {
        var note = document.createElement('div'); note.className = 'empty';
        note.textContent = 'No open times that day — try another.';
        el.appendChild(note);
      }
    });
  }

  function showMsg(text) {
    var m = document.getElementById('book-msg');
    m.textContent = text; m.classList.add('show');
  }
  function hideMsg() { document.getElementById('book-msg').classList.remove('show'); }

  function book() {
    hideMsg();
    var name = document.getElementById('f-name').value.trim();
    if (!name) { showMsg('Please enter your name.'); return; }
    if (!state.time) { showMsg('Please pick a time.'); return; }
    var btn = document.getElementById('book-btn');
    btn.disabled = true; btn.textContent = 'Booking…';
    api('/api/book', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        name: name,
        phone: document.getElementById('f-phone').value.trim(),
        email: document.getElementById('f-email').value.trim(),
        service: state.service, date: state.date, time: state.time,
        request: document.getElementById('f-request').value.trim()
      })
    }).then(function(res){
      btn.disabled = false; btn.textContent = 'Book Appointment';
      if (!res.ok) { showMsg(res.body.error || 'Something went wrong. Try again.'); return; }
      document.getElementById('r-svc').textContent = res.body.service;
      document.getElementById('r-date').textContent = res.body.date_label;
      document.getElementById('r-time').textContent = res.body.time_label;
      go('confirm');
    }).catch(function(){
      btn.disabled = false; btn.textContent = 'Book Appointment';
      showMsg('Could not reach the server. Try again.');
    });
  }

  function resetBooking() {
    document.getElementById('f-name').value = '';
    document.getElementById('f-phone').value = '';
    document.getElementById('f-email').value = '';
    document.getElementById('f-request').value = '';
    state.time = null;
    loadServices(); loadDays();
    go('booking');
  }

  loadServices();
  loadDays();

  // allow ?screen=confirm for previews
  (function(){
    var s = new URLSearchParams(location.search).get('screen');
    if (s === 'confirm') go('confirm');
  })();
</script>
</body>
</html>
"""

PORTAL_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Barber Portal</title>
<link rel="stylesheet" href="/style.css" />
</head>
<body>
<div class="stage">
  <div class="device">

    <!-- LOGIN -->
    <section id="screen-login" class="screen active">
      <div class="hero">
        <div class="logo-dot">B</div>
        <div class="brand">Barber Portal</div>
        <h1 style="margin-top:6px;">Welcome back</h1>
        <p class="sub">Sign in to see your day.</p>
      </div>
      <div class="label">Password</div>
      <div class="field"><input id="pw" type="password" placeholder="Enter your password" onkeydown="if(event.key==='Enter')login()" /></div>
      <div id="login-msg" class="msg error"></div>
      <button id="login-btn" class="btn" onclick="login()">Sign In</button>
      <p class="hint">Only you can see what's behind this login.</p>
    </section>

    <!-- TODAY'S APPOINTMENTS -->
    <section id="screen-portal" class="screen">
      <div class="topbar">
        <div class="brand">Barber Portal</div>
        <div class="back" onclick="logout()" title="Sign out">⎋</div>
      </div>
      <div class="daynav">
        <div class="arrow" onclick="changeDay(-1)">‹</div>
        <div class="today" id="day-label">—</div>
        <div class="arrow" onclick="changeDay(1)">›</div>
      </div>
      <div class="countline" id="countline">—</div>
      <div id="appt-list"></div>
    </section>

    <!-- APPOINTMENT DETAIL -->
    <section id="screen-detail" class="screen">
      <div class="backbar">
        <div class="back" onclick="go('portal')">‹</div>
        <h2>Appointment</h2>
      </div>
      <div class="client-head">
        <div class="avatar" id="d-initials">—</div>
        <div>
          <h1 id="d-name" style="font-size:22px;">—</h1>
          <p class="sub" id="d-since">—</p>
        </div>
      </div>
      <div class="contact-row">
        <a id="d-phone" href="#"></a>
        <a id="d-email" href="#"></a>
      </div>

      <div class="label">Today's booking</div>
      <div class="panel">
        <div class="row"><span class="k">Service</span><span class="v" id="d-svc">—</span></div>
        <div class="row"><span class="k">Time</span><span class="v" id="d-time">—</span></div>
        <div class="row"><span class="k">Reminder</span><span class="v" id="d-reminder">—</span></div>
        <div class="request" id="d-request"></div>
      </div>

      <div class="label notes-row"><span>Your private notes</span><button class="save-note" id="save-note" onclick="saveNotes()">Save</button></div>
      <textarea id="d-notes" rows="3"></textarea>

      <div class="label">Past visits</div>
      <div class="panel" id="d-history"></div>
      <p class="hint">Notes are private — only you ever see them.</p>
    </section>

  </div>
</div>

<script>
  var token = localStorage.getItem('barber_token') ||
              new URLSearchParams(location.search).get('token') || null;
  var current = { date: null, apptId: null };

  function authedFetch(path, opts) {
    opts = opts || {};
    opts.headers = opts.headers || {};
    opts.headers['X-Auth'] = token;
    return fetch(path, opts).then(function(r){
      return r.json().then(function(j){ return {ok:r.ok, status:r.status, body:j}; });
    });
  }
  function go(name) {
    document.querySelectorAll('.screen').forEach(function(s){ s.classList.remove('active'); });
    document.getElementById('screen-'+name).classList.add('active');
    window.scrollTo(0,0);
  }

  // ---- login ----
  function login() {
    var m = document.getElementById('login-msg'); m.classList.remove('show');
    var pw = document.getElementById('pw').value;
    var btn = document.getElementById('login-btn');
    btn.disabled = true; btn.textContent = 'Signing in…';
    fetch('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({password: pw})})
      .then(function(r){ return r.json().then(function(j){ return {ok:r.ok, body:j}; }); })
      .then(function(res){
        btn.disabled = false; btn.textContent = 'Sign In';
        if (!res.ok) { m.textContent = res.body.error || 'Wrong password.'; m.classList.add('show'); return; }
        token = res.body.token;
        localStorage.setItem('barber_token', token);
        openDay(todayISO());
        go('portal');
      });
  }
  function logout() {
    localStorage.removeItem('barber_token'); token = null;
    document.getElementById('pw').value = '';
    go('login');
  }
  function todayISO() { return new Date().toISOString().slice(0,10); }

  // ---- day view ----
  function openDay(dateISO) {
    current.date = dateISO;
    authedFetch('/api/appointments?date='+encodeURIComponent(dateISO)).then(function(res){
      if (res.status === 401) { logout(); return; }
      var d = res.body;
      document.getElementById('day-label').textContent = (d.is_today ? 'Today · ' : '') + d.date_label;
      document.getElementById('countline').textContent =
        d.count + (d.count === 1 ? ' appointment' : ' appointments') + (d.is_today ? ' today' : '');
      var el = document.getElementById('appt-list'); el.innerHTML = '';
      d.items.forEach(function(it){
        if (it.type === 'open') {
          var o = document.createElement('div'); o.className = 'open-slot';
          o.innerHTML = '<span class="time">'+it.time+'</span><span>Open</span>';
          el.appendChild(o);
        } else {
          var pill = it.reminder === 'sent'
            ? '<span class="pill sent">✓ Reminder sent</span>'
            : '<span class="pill sched">⏱ Reminder scheduled</span>';
          var a = document.createElement('div'); a.className = 'appt';
          a.innerHTML = '<span class="time">'+it.time+'</span>'+
            '<div class="who"><div class="nm">'+it.name+'</div><div class="svc">'+it.service+' · '+pill+'</div></div>'+
            '<span class="chev">›</span>';
          a.onclick = (function(id){ return function(){ openDetail(id); }; })(it.id);
          el.appendChild(a);
        }
      });
    });
  }
  function changeDay(delta) {
    var dt = new Date(current.date + 'T00:00:00');
    dt.setDate(dt.getDate() + delta);
    openDay(dt.toISOString().slice(0,10));
  }

  // ---- detail ----
  function openDetail(id) {
    current.apptId = id;
    authedFetch('/api/appointment/'+id).then(function(res){
      if (res.status === 401) { logout(); return; }
      var c = res.body;
      document.getElementById('d-initials').textContent = c.initials;
      document.getElementById('d-name').textContent = c.name;
      document.getElementById('d-since').textContent = c.since;
      var ph = document.getElementById('d-phone');
      if (c.phone) { ph.style.display=''; ph.href = 'tel:'+c.phone.replace(/[^0-9+]/g,''); ph.innerHTML = phoneIcon()+' '+c.phone; }
      else ph.style.display='none';
      var em = document.getElementById('d-email');
      if (c.email) { em.style.display=''; em.href = 'mailto:'+c.email; em.innerHTML = mailIcon()+' Email'; }
      else em.style.display='none';
      document.getElementById('d-svc').textContent = c.service;
      document.getElementById('d-time').textContent = c.time;
      document.getElementById('d-reminder').innerHTML = c.reminder === 'sent'
        ? '<span class="pill sent">✓ Sent</span>' : '<span class="pill sched">⏱ Scheduled</span>';
      var req = document.getElementById('d-request');
      if (c.request) { req.style.display='block'; req.textContent = '"'+c.request+'"'; } else req.style.display='none';
      document.getElementById('d-notes').value = c.notes;
      document.getElementById('save-note').textContent = 'Save';
      document.getElementById('save-note').classList.remove('saved');
      var h = document.getElementById('d-history'); h.innerHTML = '';
      if (!c.history.length) {
        h.innerHTML = '<p class="sub">No past visits yet — this is their first time.</p>';
      } else {
        c.history.forEach(function(v){
          var row = document.createElement('div'); row.className = 'visit';
          row.innerHTML = '<span class="d">'+v.date+'</span><span class="s">'+v.service+'</span>';
          h.appendChild(row);
        });
      }
      go('detail');
    });
  }

  function saveNotes() {
    var notes = document.getElementById('d-notes').value;
    var btn = document.getElementById('save-note');
    btn.textContent = 'Saving…';
    authedFetch('/api/appointment/'+current.apptId+'/notes', {
      method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({notes: notes})
    }).then(function(res){
      if (res.status === 401) { logout(); return; }
      btn.textContent = 'Saved ✓'; btn.classList.add('saved');
    });
  }

  function phoneIcon(){ return '<svg class="icon" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.81.36 1.6.7 2.34a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.74-1.27a2 2 0 0 1 2.11-.45c.74.34 1.53.57 2.34.7A2 2 0 0 1 22 16.92z"/></svg>'; }
  function mailIcon(){ return '<svg class="icon" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/></svg>'; }

  // ---- boot ----
  if (token) { openDay(todayISO()); go('portal'); }

  // allow ?screen=detail&appt=ID for previews (token must also be supplied)
  (function(){
    var p = new URLSearchParams(location.search);
    var s = p.get('screen');
    if (token && s === 'detail' && p.get('appt')) { openDetail(parseInt(p.get('appt'),10)); }
    else if (token && s === 'portal') { openDay(todayISO()); go('portal'); }
  })();
</script>
</body>
</html>
"""

WIDGET_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover" />
<title>Today · The Barber</title>
<!-- makes "Add to Home Screen" open full-screen, no browser bars -->
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="default" />
<meta name="apple-mobile-web-app-title" content="My Day" />
<meta name="theme-color" content="#ffffff" />
<style>
  :root { --ink:#1a1a1a; --muted:#6b7280; --line:#ececec; --soft:#f7f7f8; --ok:#1f9d55; --okbg:#e9f7ef; --warn:#9a6400; --warnbg:#fff4e5; }
  * { box-sizing:border-box; margin:0; padding:0; }
  html, body { height:100%; }
  body {
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    background:#eef0f3; color:var(--ink); -webkit-font-smoothing:antialiased;
    display:flex; align-items:center; justify-content:center;
    padding:20px; padding-top:max(20px, env(safe-area-inset-top));
  }
  .glance {
    width:100%; max-width:380px; background:#fff; border-radius:22px;
    box-shadow:0 1px 2px rgba(0,0,0,.04), 0 10px 30px rgba(0,0,0,.06);
    padding:22px; text-decoration:none; color:inherit; display:block;
  }
  .top { display:flex; align-items:center; justify-content:space-between; }
  .brand { font-size:12px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); font-weight:700; }
  .date { font-size:13px; color:var(--muted); font-weight:600; }
  .next-label { font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); font-weight:700; margin-top:18px; }
  .next { display:flex; align-items:baseline; gap:10px; margin-top:6px; }
  .next .t { font-size:30px; font-weight:800; letter-spacing:-0.02em; }
  .next .n { font-size:22px; font-weight:700; }
  .svc { color:var(--muted); font-size:14px; margin-top:2px; }
  .none { font-size:22px; font-weight:800; margin-top:14px; }
  .rest { margin-top:16px; border-top:1px solid var(--line); padding-top:12px; }
  .row { display:flex; gap:12px; padding:5px 0; font-size:15px; }
  .row .rt { font-weight:700; width:78px; flex:0 0 auto; }
  .row .rn { color:#374151; }
  .foot { display:flex; align-items:center; justify-content:space-between; margin-top:18px; }
  .chip { font-size:12px; font-weight:700; padding:5px 10px; border-radius:999px; background:var(--okbg); color:var(--ok); }
  .chip.warn { background:var(--warnbg); color:var(--warn); }
  .open { font-size:13px; color:var(--muted); font-weight:600; }
  .signin { text-align:center; }
  .signin .t { font-size:18px; font-weight:700; margin-bottom:6px; }
  .signin .s { color:var(--muted); font-size:14px; }
  .updated { text-align:center; color:#b3b8bf; font-size:11px; margin-top:12px; }
</style>
</head>
<body>
  <a class="glance" id="card" href="/portal">
    <div class="top"><span class="brand">My Day</span><span class="date" id="date"></span></div>
    <div id="content"><div class="none">Loading…</div></div>
    <div class="updated" id="updated"></div>
  </a>

<script>
  var token = localStorage.getItem('barber_token') ||
              new URLSearchParams(location.search).get('token') || null;

  function render(d) {
    document.getElementById('date').textContent = d.date_label || '';
    var c = document.getElementById('content');
    if (d.next) {
      var rest = '';
      if (d.upcoming && d.upcoming.length > 1) {
        rest = '<div class="rest">';
        for (var i = 1; i < d.upcoming.length; i++) {
          rest += '<div class="row"><span class="rt">' + d.upcoming[i].time + '</span><span class="rn">' + d.upcoming[i].name + '</span></div>';
        }
        rest += '</div>';
      }
      c.innerHTML =
        '<div class="next-label">Next up</div>' +
        '<div class="next"><span class="t">' + d.next.time + '</span><span class="n">' + d.next.name + '</span></div>' +
        '<div class="svc">' + d.next.service + '</div>' +
        rest +
        '<div class="foot"><span class="chip warn">' + d.remaining + ' left · ' + d.total + ' today</span><span class="open">Open day ›</span></div>';
    } else {
      var msg = d.total > 0 ? 'All done for today 🎉' : 'No appointments today';
      c.innerHTML =
        '<div class="none">' + msg + '</div>' +
        '<div class="foot"><span class="chip">' + (d.total > 0 ? d.total + ' seen today' : 'Nothing booked') + '</span><span class="open">Open day ›</span></div>';
    }
  }

  function showSignin() {
    document.getElementById('content').innerHTML =
      '<div class="signin"><div class="t">Tap to sign in</div><div class="s">Open your portal once to connect this glance.</div></div>';
  }

  function refresh() {
    if (!token) { showSignin(); return; }
    fetch('/api/widget', { headers: { 'X-Auth': token } })
      .then(function(r){ if (r.status === 401) { token = null; localStorage.removeItem('barber_token'); showSignin(); return null; } return r.json(); })
      .then(function(d){
        if (!d) return;
        render(d);
        var now = new Date();
        document.getElementById('updated').textContent = 'Updated ' +
          now.toLocaleTimeString([], {hour:'numeric', minute:'2-digit'});
      })
      .catch(function(){ document.getElementById('content').innerHTML = '<div class="none">Can’t reach the shop</div>'; });
  }

  // preview the "mid-day" look with sample data: open /widget?demo=1
  if (new URLSearchParams(location.search).get('demo')) {
    render({ date_label: 'Mon, Jun 15', total: 6, remaining: 3, next: { time: '2:00 PM', name: 'John Daniels', service: 'Haircut' },
      upcoming: [{time:'2:00 PM', name:'John Daniels'}, {time:'2:30 PM', name:'Will Hayes'}, {time:'3:00 PM', name:'Chris Bennett'}] });
    document.getElementById('updated').textContent = 'Updated 1:42 PM';
  } else {
  refresh();
  setInterval(refresh, 5 * 60 * 1000);          // auto-refresh every 5 min
  }
  document.addEventListener('visibilitychange', function(){ if (!document.hidden) refresh(); });
</script>
</body>
</html>
"""

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "barber.db")
PORT = int(os.environ.get("PORT", "8000"))

# The barber's portal password. Change this to whatever you like.
PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD", "barber")

# Secret key for the phone widget feed. The widget includes this in its request
# so only your phone can read your day. Change this to a long random string.
WIDGET_KEY = os.environ.get("WIDGET_KEY", "change-me-to-a-long-secret")

# Services offered (name -> minutes, price in dollars)
SERVICES = [
    {"name": "Haircut", "minutes": 45, "price": 35},
    {"name": "Haircut + Beard", "minutes": 60, "price": 50},
    {"name": "Beard Trim", "minutes": 20, "price": 20},
]
SERVICE_NAMES = {s["name"] for s in SERVICES}

# Working hours -> the bookable time slots each day (24h "HH:MM")
SLOT_TIMES = ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
              "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]

# In-memory set of valid login tokens (reset when the server restarts)
VALID_TOKENS = set()


# ---------------------------------------------------------------- database ----
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    first_time = not os.path.exists(DB_PATH)
    conn = db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            notes TEXT DEFAULT '',
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            service TEXT NOT NULL,
            price INTEGER,
            date TEXT NOT NULL,      -- YYYY-MM-DD
            time TEXT NOT NULL,      -- HH:MM
            request TEXT DEFAULT '',
            reminder TEXT DEFAULT 'scheduled',  -- 'scheduled' or 'sent'
            created_at TEXT
        );
        """
    )
    conn.commit()
    if first_time:
        seed(conn)
    conn.close()


def seed(conn):
    """Fill in a few realistic clients + appointments so the portal isn't empty."""
    today = date.today()

    def d(offset):
        return (today + timedelta(days=offset)).isoformat()

    people = [
        # name, phone, email, notes, today_time, today_service, today_price, request, past[(offset, service)]
        ("Marcus Reed", "+1 555-0142", "marcus@example.com",
         "Always early. Likes scissors over clippers on top.",
         "09:00", "Haircut", 35, "Keep the top a bit longer.",
         [(-28, "Haircut"), (-56, "Haircut"), (-84, "Haircut + Beard")]),
        ("John Daniels", "+1 555-0123", "john@example.com",
         "Likes a #2 fade on the sides. Allergic to scented products — use unscented only. Great tipper, chatty.",
         "10:00", "Haircut", 35, "Can we do a low fade this time?",
         [(-42, "Haircut"), (-70, "Haircut + Beard"), (-98, "Haircut")]),
        ("Andre Cole", "+1 555-0188", "andre@example.com",
         "Beard line on the cheek, square it off. No talking — likes it quiet.",
         "11:30", "Haircut + Beard", 50, "",
         [(-35, "Haircut + Beard"), (-63, "Beard Trim")]),
        ("Sam Okafor", "+1 555-0190", "sam@example.com",
         "New client. No history yet.",
         "13:00", "Beard Trim", 20, "First time — open to suggestions!",
         []),
        ("Will Hayes", "+1 555-0177", "will@example.com",
         "Standard taper, #1 on sides. Brings his son sometimes.",
         "14:30", "Haircut", 35, "Same as last time.",
         [(-21, "Haircut"), (-49, "Haircut"), (-77, "Haircut"), (-105, "Haircut")]),
    ]
    now = datetime.now().isoformat()
    for (name, phone, email, notes, t, svc, price, req, past) in people:
        cur = conn.execute(
            "INSERT INTO clients (name, phone, email, notes, created_at) VALUES (?,?,?,?,?)",
            (name, phone, email, notes, now),
        )
        cid = cur.lastrowid
        # past visits
        for (offset, psvc) in past:
            pprice = next((s["price"] for s in SERVICES if s["name"] == psvc), 35)
            conn.execute(
                "INSERT INTO appointments (client_id, service, price, date, time, reminder, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (cid, psvc, pprice, d(offset), "10:00", "sent", now),
            )
        # today's appointment
        reminder = "sent" if t <= "11:30" else "scheduled"
        conn.execute(
            "INSERT INTO appointments (client_id, service, price, date, time, request, reminder, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (cid, svc, price, d(0), t, req, reminder, now),
        )
    conn.commit()


# ---------------------------------------------------------------- helpers ----
def to12(hhmm):
    h, m = hhmm.split(":")
    h = int(h)
    ampm = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{m} {ampm}"


def pretty_date(iso):
    dt = datetime.strptime(iso, "%Y-%m-%d").date()
    return dt.strftime("%a, %b %-d")


def pretty_date_long(iso):
    dt = datetime.strptime(iso, "%Y-%m-%d").date()
    return dt.strftime("%b %-d, %Y")


def initials(name):
    parts = [p for p in name.split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def auth_ok(token):
    return token in VALID_TOKENS


# ---------------------------------------------------------------- handler ----
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # quiet

    # ---- small response helpers ----
    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text, content_type):
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filename, content_type):
        path = os.path.join(HERE, filename)
        try:
            with open(path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def token(self):
        # token via header or ?token= query (query is used only for screenshots)
        t = self.headers.get("X-Auth")
        if t:
            return t
        q = parse_qs(urlparse(self.path).query)
        return (q.get("token") or [None])[0]

    def body_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    # ---- routing ----
    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/" or route == "/index.html":
            return self.send_text(BOOKING_HTML, "text/html; charset=utf-8")
        if route == "/portal":
            return self.send_text(PORTAL_HTML, "text/html; charset=utf-8")
        if route == "/widget":
            return self.send_text(WIDGET_HTML, "text/html; charset=utf-8")
        if route == "/style.css":
            return self.send_text(STYLE_CSS, "text/css; charset=utf-8")
        if route == "/api/services":
            return self.send_json({"services": SERVICES})
        if route == "/api/days":
            return self.api_days()
        if route == "/api/slots":
            return self.api_slots()
        if route == "/api/widget":
            return self.api_widget()
        if route == "/api/appointments":
            return self.api_appointments()
        if route.startswith("/api/appointment/"):
            return self.api_appointment_detail(route)
        self.send_error(404)

    def do_POST(self):
        route = urlparse(self.path).path
        if route == "/api/book":
            return self.api_book()
        if route == "/api/login":
            return self.api_login()
        if route.startswith("/api/appointment/") and route.endswith("/notes"):
            return self.api_save_notes(route)
        self.send_error(404)

    # ---- public endpoints ----
    def api_days(self):
        """Next 7 days, starting today, for the booking calendar."""
        today = date.today()
        out = []
        for i in range(7):
            dt = today + timedelta(days=i)
            out.append({
                "date": dt.isoformat(),
                "dow": dt.strftime("%a"),
                "num": dt.day,
                "is_today": i == 0,
            })
        return self.send_json({"days": out})

    def api_slots(self):
        q = parse_qs(urlparse(self.path).query)
        day = (q.get("date") or [date.today().isoformat()])[0]
        conn = db()
        taken = {r["time"] for r in conn.execute(
            "SELECT time FROM appointments WHERE date=?", (day,))}
        conn.close()
        slots = [{"time": t, "label": to12(t), "taken": t in taken} for t in SLOT_TIMES]
        return self.send_json({"slots": slots})

    def api_widget(self):
        """Compact feed for the iPhone home-screen widget. Protected by WIDGET_KEY."""
        q = parse_qs(urlparse(self.path).query)
        key = (q.get("key") or [""])[0]
        # allow either the widget key OR a normal portal login token
        if key != WIDGET_KEY and not auth_ok(self.token()):
            return self.send_json({"error": "Not authorized."}, 401)
        today = date.today().isoformat()
        now_hhmm = datetime.now().strftime("%H:%M")
        conn = db()
        rows = conn.execute(
            "SELECT a.time, a.service, c.name FROM appointments a "
            "JOIN clients c ON c.id=a.client_id WHERE a.date=? ORDER BY a.time", (today,)).fetchall()
        conn.close()
        upcoming = [r for r in rows if r["time"] >= now_hhmm]
        done = len(rows) - len(upcoming)
        nxt = None
        if upcoming:
            r = upcoming[0]
            nxt = {"time": to12(r["time"]), "name": r["name"], "service": r["service"]}
        return self.send_json({
            "date_label": date.today().strftime("%a, %b %-d"),
            "total": len(rows),
            "done": done,
            "remaining": len(upcoming),
            "next": nxt,
            "upcoming": [{"time": to12(r["time"]), "name": r["name"]} for r in upcoming[:4]],
        })

    def api_book(self):
        data = self.body_json()
        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip()
        email = (data.get("email") or "").strip()
        service = (data.get("service") or "").strip()
        day = (data.get("date") or "").strip()
        time = (data.get("time") or "").strip()
        request = (data.get("request") or "").strip()

        if not name or not service or not day or not time:
            return self.send_json({"error": "Please choose a service, day, time, and enter your name."}, 400)
        if service not in SERVICE_NAMES:
            return self.send_json({"error": "Unknown service."}, 400)
        if time not in SLOT_TIMES:
            return self.send_json({"error": "Unknown time slot."}, 400)

        conn = db()
        # double-booking guard
        clash = conn.execute(
            "SELECT 1 FROM appointments WHERE date=? AND time=?", (day, time)).fetchone()
        if clash:
            conn.close()
            return self.send_json({"error": "Sorry, that time was just taken. Please pick another."}, 409)

        # reuse an existing client (match on phone or email), else create
        client = None
        if phone:
            client = conn.execute("SELECT * FROM clients WHERE phone=?", (phone,)).fetchone()
        if not client and email:
            client = conn.execute("SELECT * FROM clients WHERE email=?", (email,)).fetchone()
        now = datetime.now().isoformat()
        if client:
            cid = client["id"]
            # keep contact details fresh
            conn.execute("UPDATE clients SET name=?, phone=?, email=? WHERE id=?",
                         (name, phone or client["phone"], email or client["email"], cid))
        else:
            cur = conn.execute(
                "INSERT INTO clients (name, phone, email, notes, created_at) VALUES (?,?,?,?,?)",
                (name, phone, email, "", now))
            cid = cur.lastrowid

        price = next((s["price"] for s in SERVICES if s["name"] == service), None)
        conn.execute(
            "INSERT INTO appointments (client_id, service, price, date, time, request, reminder, created_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (cid, service, price, day, time, request, "scheduled", now))
        conn.commit()
        conn.close()
        return self.send_json({
            "ok": True,
            "service": service,
            "date_label": pretty_date(day),
            "time_label": to12(time),
        })

    def api_login(self):
        data = self.body_json()
        if (data.get("password") or "") == PORTAL_PASSWORD:
            t = secrets.token_hex(16)
            VALID_TOKENS.add(t)
            return self.send_json({"ok": True, "token": t})
        return self.send_json({"error": "Wrong password. Try again."}, 401)

    # ---- portal endpoints (require login) ----
    def api_appointments(self):
        if not auth_ok(self.token()):
            return self.send_json({"error": "Not signed in."}, 401)
        q = parse_qs(urlparse(self.path).query)
        day = (q.get("date") or [date.today().isoformat()])[0]
        conn = db()
        rows = conn.execute(
            "SELECT a.id, a.time, a.service, a.reminder, c.name "
            "FROM appointments a JOIN clients c ON c.id=a.client_id "
            "WHERE a.date=? ORDER BY a.time", (day,)).fetchall()
        conn.close()
        booked = {r["time"]: r for r in rows}
        items = []
        for t in SLOT_TIMES:
            if t in booked:
                r = booked[t]
                items.append({
                    "type": "appt", "id": r["id"], "time": to12(t),
                    "name": r["name"], "service": r["service"], "reminder": r["reminder"],
                })
            else:
                items.append({"type": "open", "time": to12(t)})
        dt = datetime.strptime(day, "%Y-%m-%d").date()
        return self.send_json({
            "date": day,
            "is_today": dt == date.today(),
            "date_label": dt.strftime("%a, %b %-d"),
            "prev": (dt - timedelta(days=1)).isoformat(),
            "next": (dt + timedelta(days=1)).isoformat(),
            "count": len(rows),
            "items": items,
        })

    def api_appointment_detail(self, route):
        if not auth_ok(self.token()):
            return self.send_json({"error": "Not signed in."}, 401)
        try:
            aid = int(route.rsplit("/", 1)[1].split("?")[0])
        except ValueError:
            return self.send_error(404)
        conn = db()
        a = conn.execute(
            "SELECT a.*, c.name, c.phone, c.email, c.notes, c.id AS cid "
            "FROM appointments a JOIN clients c ON c.id=a.client_id WHERE a.id=?",
            (aid,)).fetchone()
        if not a:
            conn.close()
            return self.send_error(404)
        # past visits = this client's other appointments, earlier than this one
        past = conn.execute(
            "SELECT date, service FROM appointments "
            "WHERE client_id=? AND id<>? AND date < ? ORDER BY date DESC",
            (a["cid"], aid, a["date"])).fetchall()
        conn.close()
        since = None
        if past:
            oldest = past[-1]["date"]
            since = "Client since " + oldest[:4]
        else:
            since = "New client"
        return self.send_json({
            "id": a["id"],
            "name": a["name"],
            "initials": initials(a["name"]),
            "since": since,
            "phone": a["phone"] or "",
            "email": a["email"] or "",
            "service": a["service"],
            "time": to12(a["time"]),
            "reminder": a["reminder"],
            "request": a["request"] or "",
            "notes": a["notes"] or "",
            "history": [{"date": pretty_date_long(p["date"]), "service": p["service"]} for p in past],
        })

    def api_save_notes(self, route):
        if not auth_ok(self.token()):
            return self.send_json({"error": "Not signed in."}, 401)
        try:
            aid = int(route.split("/api/appointment/")[1].split("/notes")[0])
        except (ValueError, IndexError):
            return self.send_error(404)
        data = self.body_json()
        notes = data.get("notes", "")
        conn = db()
        a = conn.execute("SELECT client_id FROM appointments WHERE id=?", (aid,)).fetchone()
        if not a:
            conn.close()
            return self.send_error(404)
        conn.execute("UPDATE clients SET notes=? WHERE id=?", (notes, a["client_id"]))
        conn.commit()
        conn.close()
        return self.send_json({"ok": True})


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


if __name__ == "__main__":
    init_db()
    with ThreadingServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"The Barber running at http://localhost:{PORT}  (portal password: {PORTAL_PASSWORD})")
        httpd.serve_forever()

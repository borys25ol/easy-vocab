// RANK CONFIGURATION LOGIC
function getRankConfig(group, type) {
    const g = group ? group.toLowerCase() : '';
    const t = type ? type.toLowerCase() : 'word';
    const styles = {
        green: {badge: 'bg-green-100 text-green-700 border-green-200'},
        teal: {badge: 'bg-teal-100 text-teal-700 border-teal-200'},
        blue: {badge: 'bg-blue-100 text-blue-700 border-blue-200'},
        indigo: {badge: 'bg-indigo-100 text-indigo-700 border-indigo-200'},
        purple: {badge: 'bg-purple-100 text-purple-700 border-purple-200'},
        orange: {badge: 'bg-orange-100 text-orange-700 border-orange-200'}
    };

    if (t === 'phrase') {
        if (g.includes('very common')) return styles.green;
        if (g.includes('common')) return styles.blue;
        if (g.includes('less common')) return styles.indigo;
        return styles.orange;
    } else {
        if (g.includes('core 500')) return styles.green;
        if (g.includes('core 1000')) return styles.teal;
        if (g.includes('core plus')) return styles.blue;
        if (g.includes('active basic')) return styles.indigo;
        if (g.includes('fluent') || g.includes('active extended') || g.includes('advanced')) return styles.purple;
        return styles.orange;
    }
}

// LEFT BORDER COLOR LOGIC (BY CEFR LEVEL)
function getLevelBorderClass(level) {
    const lvl = (level || 'A1').toUpperCase();
    if (lvl.includes('A1')) return 'lvl-a1';
    if (lvl.includes('A2')) return 'lvl-a2';
    if (lvl.includes('B1')) return 'lvl-b1';
    if (lvl.includes('B2')) return 'lvl-b2';
    if (lvl.includes('C1')) return 'lvl-c1';
    if (lvl.includes('C2')) return 'lvl-c2';
    return 'lvl-a1';
}

// CEFR LEVEL DOT STYLE LOGIC
function getLevelDotStyle(level) {
    const lvl = (level || 'A1').toUpperCase();
    const colors = {
        'A1': 'text-green-500',
        'A2': 'text-yellow-500',
        'B1': 'text-blue-500',
        'B2': 'text-purple-500',
        'C1': 'text-orange-500',
        'C2': 'text-red-500'
    };
    const key = Object.keys(colors).find(k => lvl.includes(k)) || 'A1';
    return colors[key];
}

// TOGGLE CARD DETAILS
function toggleDetails(id) {
    document.getElementById(`card-${id}`).classList.toggle('card-active');
}

// TEXT TO SPEECH LOGIC
function speak(text) {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    const v = window.speechSynthesis.getVoices();
    u.voice = v.find(v => v.lang.startsWith('en-US')) || v.find(v => v.lang.startsWith('en'));
    u.rate = 0.9;
    window.speechSynthesis.speak(u);
}

// FUNCTION TO RENDER INDIVIDUAL WORD CARD HTML
//
// Everything interpolated here reaches innerHTML, so every field goes through
// escapeHtml from shared.js. Handlers read their arguments from data
// attributes rather than taking them inline, because a quote in the value
// would otherwise close the attribute and inject markup of its own.
function renderWordCard(word) {
    // Get styles from shared.js logic
    const rankConfig = getRankConfig(word.frequency_group, word.type);
    const borderClass = getLevelBorderClass(word.level);
    const dotStyle = getLevelDotStyle(word.level);

    // Parse synonyms list (split by newline for consistency)
    const synonymsList = word.synonyms && word.synonyms !== "Synonyms not found"
        ? word.synonyms.split('\n').map(syn =>
            `<div class="text-indigo-500 font-medium">• ${escapeHtml(syn.trim())}</div>`
        ).join('\n')
        : '<span class="text-slate-300 italic text-xs">No synonyms found</span>';

    const examples = word.examples
        ? word.examples.split('\n').map(escapeHtml).join('<br>')
        : 'No examples';

    // Build the card HTML template
    return `
        <div id="card-${word.id}" class="bg-white p-5 rounded-2xl shadow-sm transition-all ${borderClass} ${word.is_learned ? 'opacity-50 grayscale-[0.6]' : ''}">
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <div class="flex items-center flex-wrap gap-2">
                        <h3 class="text-xl font-bold text-slate-800">${escapeHtml(word.word)}</h3>
                        <button type="button" data-speak="${escapeHtml(word.word)}" onclick="speakFromButton(this)" class="text-slate-300 hover:text-indigo-500 p-1">
                            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77zM16.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM7 9H3v6h4l5 5V4L7 9z"/></svg>
                        </button>
                        <span class="px-2 py-0.5 text-[9px] font-black uppercase tracking-wider rounded border ${rankConfig.badge}">
                            ${escapeHtml(word.frequency_group)} ${word.rank ? '#' + escapeHtml(word.rank) : ''}
                        </span>
                        <div class="flex items-center gap-1 text-[11px] font-bold text-slate-500">
                            <span class="${dotStyle} text-[14px]">●</span>
                            <span>${escapeHtml(word.level || 'A1')}</span>
                        </div>
                    </div>

                    <button onclick="toggleDetails(${word.id})" class="mt-2 text-indigo-500 text-[11px] font-bold flex items-center gap-1 uppercase">
                        <span>Details</span>
                        <svg class="chevron w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7"></path></svg>
                    </button>

                    <div class="details-container">
                        <div class="blur-text border-t border-slate-50 pt-3">
                            <p class="text-indigo-600 font-black text-xl mb-3">${escapeHtml(word.translation)}</p>
                            <div class="text-sm text-slate-500 italic border-l-2 border-slate-200 pl-4">
                                ${examples}
                            </div>
                        </div>

                        <div class="mt-4">
                            <span class="text-[9px] font-black text-slate-400 uppercase tracking-widest block mb-1">Synonyms</span>
                            <div class="space-y-1 text-sm">
                                ${synonymsList}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="flex items-center gap-1 ml-4">
                    <button onclick="toggleLearned(${word.id})" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-green-50">${word.is_learned ? '✅' : '✔️'}</button>
                    <button type="button" data-id="${word.id}" data-word="${escapeHtml(word.word)}" data-translation="${escapeHtml(word.translation)}" data-category="${escapeHtml(word.category)}" onclick="openEditModalFromButton(this)" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-indigo-50 text-slate-400">✏️</button>
                    <button onclick="requestDelete(${word.id})" class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-red-50 text-slate-400">🗑️</button>
                </div>
            </div>
        </div>
    `;
}

/** Format limited model markdown while escaping provider output before inserting HTML. */
export function formatAiContent(text, replaceBullets = false) {
	const escaped = text.replace(/[&<>"']/g, (char) => ({
		'&': '&amp;',
		'<': '&lt;',
		'>': '&gt;',
		'"': '&quot;',
		"'": '&#39;',
	}[char] ?? char));
	const formatted = escaped
		.replace(/\n/g, '<br>')
		.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
	return replaceBullets ? formatted.replace(/^[-•]\s/gm, '• ') : formatted;
}

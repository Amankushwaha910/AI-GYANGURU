import test from 'node:test';
import assert from 'node:assert/strict';
import { formatAiContent } from '../src/lib/formatAiContent.mjs';

test('escapes HTML from model content while preserving simple formatting', () => {
	assert.equal(
		formatAiContent('<img src=x onerror="alert(1)"> **safe**\nnext'),
		'&lt;img src=x onerror=&quot;alert(1)&quot;&gt; <strong>safe</strong><br>next'
	);
});

test('formats requested bullets after escaping model output', () => {
	assert.equal(formatAiContent('- <script>\n• item', true), '• &lt;script&gt;<br>• item');
});

<script lang="ts">
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$stores/auth';
	import { onMount } from 'svelte';
	import { GraduationCap, BookOpen, Lightbulb, HelpCircle, BarChart2 } from 'lucide-svelte';
	import Button from '$components/ui/Button.svelte';

	onMount(() => {
		if ($isAuthenticated) goto('/dashboard');
	});

	const features = [
		{ icon: BookOpen, title: 'Smart Summaries', desc: 'Instant revision notes, key concepts, and exam tips for any topic.' },
		{ icon: Lightbulb, title: 'Deep Explanations', desc: 'Step-by-step breakdowns with real examples and analogies.' },
		{ icon: HelpCircle, title: 'AI Quizzes', desc: 'Auto-generated MCQs with detailed explanations for every answer.' },
		{ icon: BarChart2, title: 'Progress Analytics', desc: 'Track what you know, identify weak areas, and improve fast.' }
	];
</script>

<svelte:head>
	<title>AI GyanGuru — Your Intelligent Study Companion</title>
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-brand-950 via-gray-950 to-gray-900 text-white">
	<!-- Nav -->
	<nav class="flex items-center justify-between px-8 py-5 max-w-7xl mx-auto">
		<div class="flex items-center gap-3">
			<div class="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500">
				<GraduationCap class="h-5 w-5 text-white" />
			</div>
			<span class="font-bold text-lg">AI GyanGuru</span>
		</div>
		<div class="flex items-center gap-3">
			<Button href="/login" variant="ghost" class="text-gray-300 hover:text-white hover:bg-white/10">Login</Button>
			<Button href="/register" variant="primary">Get Started Free</Button>
		</div>
	</nav>

	<!-- Hero -->
	<section class="max-w-4xl mx-auto px-8 py-24 text-center">
		<div class="inline-flex items-center gap-2 rounded-full bg-brand-500/20 border border-brand-500/30 px-4 py-1.5 text-sm text-brand-300 mb-6">
			<span class="h-1.5 w-1.5 rounded-full bg-brand-400"></span>
			Powered by Groq · Llama 3 · DeepSeek R1
		</div>
		<h1 class="text-5xl font-bold leading-tight mb-6">
			Learn Smarter with<br />
			<span class="bg-gradient-to-r from-brand-400 to-purple-400 bg-clip-text text-transparent">
				AI-Powered Study Tools
			</span>
		</h1>
		<p class="text-xl text-gray-300 mb-10 max-w-2xl mx-auto leading-relaxed">
			Enter any topic or upload your study material. AI GyanGuru instantly generates summaries,
			explanations, quizzes, and tracks your progress — all in one place.
		</p>
		<div class="flex items-center justify-center gap-4">
			<Button href="/register" size="lg" variant="primary">Start Learning Free</Button>
			<Button href="/login" size="lg" variant="outline" class="border-white/30 text-white hover:bg-white/10">Sign In</Button>
		</div>
	</section>

	<!-- Features -->
	<section class="max-w-6xl mx-auto px-8 pb-24">
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
			{#each features as f}
				<div class="rounded-2xl border border-white/10 bg-white/5 p-6 hover:bg-white/10 transition-colors">
					<div class="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/20">
						<svelte:component this={f.icon} class="h-5 w-5 text-brand-400" />
					</div>
					<h3 class="font-semibold text-white mb-2">{f.title}</h3>
					<p class="text-sm text-gray-400 leading-relaxed">{f.desc}</p>
				</div>
			{/each}
		</div>
	</section>
</div>

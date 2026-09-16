<script lang="ts">
	import { base } from '$app/paths';
	import { site } from '$lib/site';
</script>

<footer class="foot">
	<div class="shell">
		<div class="cols">
			<div>
				<p class="eyebrow eyebrow--plain">Spec</p>
				<ul>
					<li><a href="{base}/spec/v1/">Version 1 specification</a></li>
					<li><a href="{base}/spec/words-v1/">Transcript body</a></li>
					<li><a href="{base}/spec/audio-integrity/">Audio digest</a></li>
					<li><a href="{base}/schema/">JSON Schemas</a></li>
					<li><a href="{base}/changelog/">Changelog</a></li>
					<li><a href="{base}/design/">Design notes</a></li>
					<li><a href="{base}/llms-full.txt">Complete specification as text</a></li>
				</ul>
			</div>
			<div>
				<p class="eyebrow eyebrow--plain">Tools</p>
				<ul>
					<li><a href="{base}/try/">Open a file</a></li>
					<li><a href="{base}/consume/">Read a file in code</a></li>
					<li><a href="{base}/produce/">Create a Cassini file</a></li>
					<li>
						<a href="{base}/build/#check-a-file-then-test-your-implementation">Conformance</a>
					</li>
					<li><a href={site.repo} rel="noreferrer">Source on GitHub ↗</a></li>
				</ul>
			</div>
			<div>
				<p class="eyebrow eyebrow--plain">Implementations</p>
				<ul>
					<li><a href={site.appUrl} rel="noreferrer">{site.appName} ↗</a></li>
					<li><a href={site.implRepo} rel="noreferrer">{site.appName} on GitHub ↗</a></li>
					<li>
						<a href="https://apps.nextcloud.com/apps/gocassini" rel="noreferrer"
							>Nextcloud App Store ↗</a
						>
					</li>
					<li><a href="{site.repo}/issues" rel="noreferrer">Report an implementation ↗</a></li>
				</ul>
			</div>
		</div>

		<div class="rule"></div>

		<div class="legal">
			<a class="cm" href={site.companyUrl} rel="noreferrer">
				<svg width="18" height="14" viewBox="0 0 160 121" fill="none" aria-hidden="true">
					<path d="M74.4642 115.541H85.3733V99.1653H74.4642V115.541Z" fill="currentColor" />
					<path
						d="M44.4605 5.54444L34.8728 -9.34149e-05L0 60.4998L34.4823 120.322L44.07 114.778L12.7833 60.4998L44.4605 5.54444Z"
						fill="currentColor"
					/>
					<path
						d="M125.127 0.000192144L115.539 5.54472L147.217 60.5001L115.539 115.455L125.127 121L160 60.5001L125.127 0.000192144Z"
						fill="currentColor"
					/>
					<path d="M85.3742 6.36844H74.4651V22.7444H85.3742V6.36844Z" fill="currentColor" />
					<path d="M42.5952 55.4963H26.2316V66.4136H42.5952V55.4963Z" fill="currentColor" />
					<path
						d="M86.869 54.5864H73.132H66.1764H64.5455V60.0454V65.5037H66.1764H73.132H86.869H93.8246H95.4546V60.0454V54.5864H93.8246H86.869Z"
						fill="currentColor"
					/>
					<path d="M117.918 66.4136H134.281V55.4963H117.918V66.4136Z" fill="currentColor" />
					<path
						d="M101.818 60.9548C101.818 48.8959 92.0498 39.1202 80 39.1202C67.9501 39.1202 58.1818 48.8959 58.1818 60.9548C58.1818 73.0137 67.9501 82.7894 80 82.7894V93.7067C61.9252 93.7067 47.2727 79.0431 47.2727 60.9548C47.2727 42.8664 61.9252 28.2029 80 28.2029C98.0747 28.2029 112.727 42.8664 112.727 60.9548C112.727 79.0431 98.0747 93.7067 80 93.7067V82.7894C92.0498 82.7894 101.818 73.0137 101.818 60.9548Z"
						fill="currentColor"
					/>
				</svg>
				<span>{site.company}</span>
			</a>
			<p class="lic">
				Spec text <a href="https://creativecommons.org/licenses/by/4.0/" rel="noreferrer"
					>CC&nbsp;BY&nbsp;4.0</a
				>. Schemas, test vectors and standalone readers/producer
				<a href="https://creativecommons.org/publicdomain/zero/1.0/" rel="noreferrer"
					>CC0&nbsp;1.0</a
				>. Cassini’s transcript component
				<a href="{site.repo}/blob/main/site/src/lib/vendor/cassini-viewer/README.md">AGPL-3.0</a>.
			</p>
		</div>
	</div>
</footer>

<style>
	.foot {
		border-top: 1px solid var(--rule);
		margin-top: 6rem;
		padding: 3rem 0 3.5rem;
		font-size: 13px;
	}
	.cols {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 2.5rem;
	}
	@media (max-width: 820px) {
		.cols {
			grid-template-columns: 1fr;
			gap: 2rem;
		}
	}
	.eyebrow {
		margin-bottom: 0.9rem;
	}
	ul {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		gap: 0.4rem;
	}
	ul a {
		color: var(--fg-3);
	}
	ul a:hover {
		color: var(--fg);
	}
	.rule {
		height: 1px;
		background: var(--rule);
		margin: 2.5rem 0 1.5rem;
	}
	.legal {
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 1rem 2rem;
		justify-content: space-between;
	}
	.cm {
		display: inline-flex;
		align-items: center;
		gap: 0.55rem;
		color: var(--fg-3);
		flex: none;
	}
	.cm:hover {
		color: var(--fg);
		text-decoration: none;
	}
	.lic {
		margin: 0;
		color: var(--fg-4);
		font-size: 12px;
		max-width: 62ch;
	}
	.lic a {
		color: var(--fg-3);
	}
</style>

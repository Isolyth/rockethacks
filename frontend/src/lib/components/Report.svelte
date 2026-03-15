<script lang="ts">
	import DOMPurify from "isomorphic-dompurify";
	import type { FinancialReport, PieSegment, DailySpending } from "$lib/types";

	let {
		report,
		pieSegments = null,
		dailySpending = null,
	}: {
		report: FinancialReport;
		pieSegments?: PieSegment[] | null;
		dailySpending?: DailySpending[] | null;
	} = $props();

	let activeChart = $state<"bar" | "doughnut" | "heatmap">("bar");
	let hoveredDay = $state<{ date: string; total: number; x: number; y: number } | null>(null);
	let heatmapMonthIndex = $state(0);

	function formatCurrency(n: number): string {
		return new Intl.NumberFormat("en-US", {
			style: "currency",
			currency: "USD",
		}).format(n);
	}

	function formatCompact(n: number): string {
		if (n >= 1000) return `$${(n / 1000).toFixed(1)}k`;
		return `$${n.toFixed(0)}`;
	}

	const maxCategoryTotal = $derived(
		Math.max(...report.categories.map((c) => c.total), 1),
	);

	const categoryColors = [
		"#4361EE",
		"#3A0CA3",
		"#7209B7",
		"#F72585",
		"#4CC9F0",
		"#00B4D8",
		"#0077B6",
		"#023E8A",
	];

	// Doughnut chart computed values
	const DONUT_RADIUS = 80;
	const DONUT_CIRCUMFERENCE = 2 * Math.PI * DONUT_RADIUS;

	const donutSegments = $derived(() => {
		const segs = pieSegments ?? [];
		if (segs.length === 0) return [];
		let cumulative = 0;
		return segs.map((seg, i) => {
			const dashLength = (seg.percentage / 100) * DONUT_CIRCUMFERENCE;
			const dashGap = DONUT_CIRCUMFERENCE - dashLength;
			const offset = -(cumulative / 100) * DONUT_CIRCUMFERENCE;
			cumulative += seg.percentage;
			return {
				...seg,
				color: categoryColors[i % categoryColors.length],
				dashArray: `${dashLength} ${dashGap}`,
				dashOffset: offset,
			};
		});
	});

	// Heatmap computed values — grouped by month for multi-month support
	interface HeatmapDay { date: string; day: number; total: number; inRange: boolean }
	interface HeatmapMonth { label: string; weeks: HeatmapDay[][] }

	const heatmapData = $derived(() => {
		const data = dailySpending ?? [];
		if (data.length === 0) return { months: [] as HeatmapMonth[], dayLabels: [] as string[], maxTotal: 0 };

		const sorted = [...data].sort((a, b) => a.date.localeCompare(b.date));
		const maxTotal = Math.max(...sorted.map((d) => d.total), 1);
		const dayMap = new Map(sorted.map((d) => [d.date, d.total]));

		const startDate = new Date(sorted[0].date + "T00:00:00");
		const endDate = new Date(sorted[sorted.length - 1].date + "T00:00:00");

		// Build month-by-month grids
		const months: HeatmapMonth[] = [];
		let cur = new Date(startDate.getFullYear(), startDate.getMonth(), 1);

		while (cur <= endDate) {
			const year = cur.getFullYear();
			const month = cur.getMonth();
			const daysInMonth = new Date(year, month + 1, 0).getDate();
			const label = cur.toLocaleDateString("en-US", { month: "short", year: "numeric" });

			// Find what weekday the 1st falls on (Mon=0 .. Sun=6)
			const firstDow = (new Date(year, month, 1).getDay() + 6) % 7;

			const weeks: HeatmapDay[][] = [];
			let week: HeatmapDay[] = [];

			// Leading empty cells
			for (let p = 0; p < firstDow; p++) {
				week.push({ date: "", day: 0, total: 0, inRange: false });
			}

			for (let d = 1; d <= daysInMonth; d++) {
				const dateObj = new Date(year, month, d);
				const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
				const inRange = dateObj >= startDate && dateObj <= endDate;
				week.push({
					date: dateStr,
					day: d,
					total: dayMap.get(dateStr) ?? 0,
					inRange,
				});
				if (week.length === 7) {
					weeks.push(week);
					week = [];
				}
			}

			// Trailing empty cells
			if (week.length > 0) {
				while (week.length < 7) {
					week.push({ date: "", day: 0, total: 0, inRange: false });
				}
				weeks.push(week);
			}

			months.push({ label, weeks });
			cur = new Date(year, month + 1, 1);
		}

		return { months, dayLabels: ["M", "T", "W", "T", "F", "S", "S"], maxTotal };
	});

	function heatmapColor(total: number, max: number): string {
		if (total === 0) return "rgba(67, 97, 238, 0.08)";
		const intensity = Math.min(total / max, 1);
		// Scale from low (dim blue) to high (bright magenta)
		const r = Math.round(67 + (247 - 67) * intensity);
		const g = Math.round(97 + (37 - 97) * intensity);
		const b = Math.round(238 + (133 - 238) * intensity);
		const alpha = 0.3 + 0.7 * intensity;
		return `rgba(${r}, ${g}, ${b}, ${alpha})`;
	}

	function handleDayHover(e: MouseEvent, day: HeatmapDay) {
		if (!day.inRange || day.day === 0) return;
		const rect = (e.target as HTMLElement).getBoundingClientRect();
		const parent = (e.target as HTMLElement).closest('.heatmap-container')?.getBoundingClientRect();
		if (!parent) return;
		hoveredDay = {
			date: day.date,
			total: day.total,
			x: rect.left - parent.left + rect.width / 2,
			y: rect.top - parent.top - 8,
		};
	}
</script>

<div class="report">
	<h2>Financial Report</h2>
	<p class="date-range">{report.summary.date_range}</p>

	<div class="summary-cards">
		<div class="card income">
			<span class="card-label">Income</span>
			<span class="card-value"
				>{formatCurrency(report.summary.total_income)}</span
			>
		</div>
		<div class="card expenses">
			<span class="card-label">Expenses</span>
			<span class="card-value"
				>{formatCurrency(report.summary.total_expenses)}</span
			>
		</div>
		<div
			class="card savings"
			class:negative={report.summary.net_savings < 0}
		>
			<span class="card-label">Net Savings</span>
			<span class="card-value"
				>{formatCurrency(report.summary.net_savings)}</span
			>
		</div>
	</div>

	<section class="section">
		<h3>Spending by Category</h3>

		<!-- Chart selector -->
		<div class="chart-selector">
			<button
				class="chart-tab"
				class:active={activeChart === "bar"}
				onclick={() => (activeChart = "bar")}
				type="button"
			>
				Bar
			</button>
			<button
				class="chart-tab"
				class:active={activeChart === "doughnut"}
				onclick={() => (activeChart = "doughnut")}
				type="button"
			>
				Doughnut
			</button>
			<button
				class="chart-tab"
				class:active={activeChart === "heatmap"}
				onclick={() => (activeChart = "heatmap")}
				type="button"
			>
				Heatmap
			</button>
		</div>

		<!-- Bar chart (existing) -->
		{#if activeChart === "bar"}
			<div class="categories">
				{#each report.categories as cat, i}
					<div class="category-row">
						<div class="category-info">
							<span class="category-name">{cat.name}</span>
							<span class="category-amount"
								>{formatCurrency(cat.total)}</span
							>
						</div>
						<div class="category-bar-track">
							<div
								class="category-bar-fill"
								style="width: {(cat.total / maxCategoryTotal) *
									100}%; background: {categoryColors[
									i % categoryColors.length
								]}"
							></div>
						</div>
						<span class="category-pct"
							>{cat.percentage.toFixed(1)}%</span
						>
					</div>
				{/each}
			</div>

		<!-- Doughnut chart -->
		{:else if activeChart === "doughnut"}
			{#if pieSegments && pieSegments.length > 0}
				<div class="doughnut-container">
					<svg viewBox="0 0 200 200" class="doughnut-svg">
						{#each donutSegments() as seg}
							<circle
								cx="100"
								cy="100"
								r={DONUT_RADIUS}
								fill="none"
								stroke={seg.color}
								stroke-width="24"
								stroke-dasharray={seg.dashArray}
								stroke-dashoffset={seg.dashOffset}
								stroke-linecap="butt"
								transform="rotate(-90 100 100)"
							/>
						{/each}
						<text x="100" y="96" text-anchor="middle" class="donut-total">
							{formatCompact(report.summary.total_expenses)}
						</text>
						<text x="100" y="114" text-anchor="middle" class="donut-label">
							total spent
						</text>
					</svg>
					<div class="doughnut-legend">
						{#each donutSegments() as seg, i}
							<div class="legend-item">
								<span
									class="legend-dot"
									style="background: {seg.color}"
								></span>
								<span class="legend-name">{seg.name}</span>
								<span class="legend-value"
									>{seg.percentage.toFixed(1)}%</span
								>
							</div>
						{/each}
					</div>
				</div>
			{:else}
				<div class="chart-loading">
					<div class="skeleton-donut">
						<div class="skeleton-ring"></div>
					</div>
					<p class="loading-text">Generating doughnut chart...</p>
				</div>
			{/if}

		<!-- Heatmap -->
		{:else if activeChart === "heatmap"}
			{#if dailySpending && dailySpending.length > 0}
				{@const hm = heatmapData()}
				{@const month = hm.months[heatmapMonthIndex] ?? hm.months[0]}
				{@const hasPrev = heatmapMonthIndex > 0}
				{@const hasNext = heatmapMonthIndex < hm.months.length - 1}
				<div class="heatmap-container" role="img" aria-label="Daily spending heatmap">
					<div class="heatmap-nav">
						{#if hasPrev}
							<button
								class="heatmap-arrow"
								type="button"
								onclick={() => { heatmapMonthIndex--; hoveredDay = null; }}
								aria-label="Previous month"
							>&#8592;</button>
						{:else}
							<div class="heatmap-arrow-spacer"></div>
						{/if}
						<h4 class="month-label">{month.label}</h4>
						{#if hasNext}
							<button
								class="heatmap-arrow"
								type="button"
								onclick={() => { heatmapMonthIndex++; hoveredDay = null; }}
								aria-label="Next month"
							>&#8594;</button>
						{:else}
							<div class="heatmap-arrow-spacer"></div>
						{/if}
					</div>
					<div class="heatmap-day-labels">
						{#each hm.dayLabels as label}
							<span class="day-label">{label}</span>
						{/each}
					</div>
					<div class="heatmap-grid">
						{#each month.weeks as week}
							<div class="heatmap-week">
								{#each week as day}
									{#if day.day === 0}
										<div class="heatmap-cell empty"></div>
									{:else}
										<div
											class="heatmap-cell"
											class:out-of-range={!day.inRange}
											style="background: {day.inRange
												? heatmapColor(day.total, hm.maxTotal)
												: 'rgba(67, 97, 238, 0.04)'}"
											onmouseenter={(e) => handleDayHover(e, day)}
											onmouseleave={() => (hoveredDay = null)}
											role="presentation"
										>
											<span class="cell-date">{day.day}</span>
										</div>
									{/if}
								{/each}
							</div>
						{/each}
					</div>
					{#if hoveredDay}
						<div
							class="heatmap-tooltip"
							style="left: {hoveredDay.x}px; top: {hoveredDay.y}px"
						>
							<span class="tooltip-date">{hoveredDay.date}</span>
							<span class="tooltip-amount"
								>{formatCurrency(hoveredDay.total)}</span
							>
						</div>
					{/if}
					<div class="heatmap-legend">
						<span class="legend-label">Less</span>
						<div class="legend-scale">
							{#each [0, 0.25, 0.5, 0.75, 1] as intensity}
								<div
									class="legend-cell"
									style="background: {heatmapColor(
										intensity * (hm.maxTotal || 1),
										hm.maxTotal || 1,
									)}"
								></div>
							{/each}
						</div>
						<span class="legend-label">More</span>
					</div>
				</div>
			{:else}
				<div class="chart-loading">
					<div class="skeleton-grid">
						{#each Array(5) as _}
							<div class="skeleton-row">
								{#each Array(7) as _}
									<div class="skeleton-cell"></div>
								{/each}
							</div>
						{/each}
					</div>
					<p class="loading-text">Generating heatmap...</p>
				</div>
			{/if}
		{/if}
	</section>

	{#if report.top_merchants.length > 0}
		<section class="section">
			<h3>Top Merchants</h3>
			<div class="merchants">
				{#each report.top_merchants as merchant}
					<div class="merchant-row">
						<span class="merchant-name">{merchant.name}</span>
						<span class="merchant-count">{merchant.count} txns</span
						>
						<span class="merchant-total"
							>{formatCurrency(merchant.total)}</span
						>
					</div>
				{/each}
			</div>
		</section>
	{/if}

	{#if report.insights.length > 0}
		<section class="section">
			<h3>Insights</h3>
			<ul class="insights">
				{#each report.insights as insight}
					<li>{insight}</li>
				{/each}
			</ul>
		</section>
	{/if}

	{#if report.grounding?.sources && report.grounding.sources.length > 0}
		<section class="section">
			<h3>Sources</h3>
			<ul class="sources">
				{#each report.grounding.sources as source}
					<li class="source-item">
						<a href={source.uri} target="_blank" rel="noopener noreferrer">
							{source.title || source.domain || source.uri}
						</a>
						{#if source.domain}
							<span class="source-domain">{source.domain}</span>
						{/if}
					</li>
				{/each}
			</ul>
		</section>
	{/if}

	{#if report.grounding?.search_entry_point_html}
		<section class="section search-entry-point">
			{@html DOMPurify.sanitize(report.grounding.search_entry_point_html)}
		</section>
	{/if}
</div>

<style>
	.report {
		width: 100%;
		background: var(--color-surface);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border-radius: var(--radius);
		border: 1px solid var(--color-border);
		padding: 2rem;
		box-shadow: var(--shadow-inset);
		animation: fadeInUp 0.5s ease both;
	}

	h2 {
		font-size: 1.5rem;
		margin-bottom: 0.25rem;
	}

	.date-range {
		color: var(--color-text-muted);
		font-size: 0.875rem;
		margin-bottom: 1.5rem;
	}

	.summary-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.card {
		background: var(--color-surface);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		border: 1px solid var(--color-border);
		border-radius: var(--radius);
		padding: 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		box-shadow: var(--shadow-inset);
		animation: fadeInScale 0.4s ease both;
	}

	.card:nth-child(1) { animation-delay: 0.1s; }
	.card:nth-child(2) { animation-delay: 0.2s; }
	.card:nth-child(3) { animation-delay: 0.3s; }

	.card-label {
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-muted);
	}

	.card-value {
		font-size: 1.5rem;
		font-weight: 700;
	}

	.card.income .card-value {
		color: var(--color-success);
	}

	.card.expenses .card-value {
		color: var(--color-danger);
	}

	.card.savings .card-value {
		color: var(--color-success);
	}

	.card.savings.negative .card-value {
		color: var(--color-danger);
	}

	.section {
		margin-bottom: 2rem;
	}

	.section h3 {
		font-size: 1.1rem;
		margin-bottom: 1rem;
		color: var(--color-text);
	}

	/* Chart selector */
	.chart-selector {
		display: flex;
		gap: 0;
		margin-bottom: 1.25rem;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		overflow: hidden;
	}

	.chart-tab {
		flex: 1;
		padding: 0.6rem 1rem;
		background: transparent;
		color: var(--color-text-muted);
		border: none;
		font-size: 0.85rem;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s ease;
		position: relative;
	}

	.chart-tab:not(:last-child) {
		border-right: 1px solid var(--color-border);
	}

	.chart-tab:hover {
		color: var(--color-text);
		background: var(--color-surface-2);
	}

	.chart-tab.active {
		color: #0a0a0f;
		background: var(--gradient-gold-btn);
		font-weight: 600;
	}

	/* Bar chart */
	.categories {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.category-row {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.category-info {
		width: 200px;
		flex-shrink: 0;
		display: flex;
		justify-content: space-between;
		gap: 0.5rem;
	}

	.category-name {
		font-size: 0.875rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.category-amount {
		font-size: 0.875rem;
		color: var(--color-text-muted);
		flex-shrink: 0;
	}

	.category-bar-track {
		flex: 1;
		height: 8px;
		background: var(--color-surface);
		border-radius: 4px;
		overflow: hidden;
	}

	.category-bar-fill {
		height: 100%;
		border-radius: 4px;
		transition: width 0.5s ease;
	}

	.category-pct {
		width: 48px;
		text-align: right;
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	/* Doughnut chart */
	.doughnut-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1.5rem;
		animation: fadeIn 0.4s ease both;
	}

	.doughnut-svg {
		width: 200px;
		height: 200px;
	}

	.donut-total {
		fill: var(--color-text);
		font-size: 18px;
		font-weight: 700;
	}

	.donut-label {
		fill: var(--color-text-muted);
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.doughnut-legend {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem 1.25rem;
		justify-content: center;
	}

	.legend-item {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.8rem;
	}

	.legend-dot {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.legend-name {
		color: var(--color-text);
	}

	.legend-value {
		color: var(--color-text-muted);
	}

	/* Heatmap */
	.heatmap-container {
		position: relative;
		animation: fadeIn 0.4s ease both;
		display: flex;
		flex-direction: column;
		gap: 0;
	}

	.heatmap-nav {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin-bottom: 0.5rem;
	}

	.heatmap-arrow {
		background: transparent;
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		color: var(--color-text-muted);
		font-size: 1rem;
		width: 28px;
		height: 28px;
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		transition: all 0.15s ease;
		padding: 0;
		line-height: 1;
	}

	.heatmap-arrow:hover {
		color: var(--color-text);
		border-color: var(--color-accent);
		background: var(--color-surface-2);
	}

	.heatmap-arrow-spacer {
		width: 28px;
		height: 28px;
	}

	.month-label {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--color-text);
		margin: 0;
		min-width: 100px;
		text-align: center;
	}

	.heatmap-day-labels {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 2px;
		margin-bottom: 2px;
	}

	.day-label {
		text-align: center;
		font-size: 0.6rem;
		color: var(--color-text-muted);
	}

	.heatmap-grid {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.heatmap-week {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 2px;
	}

	.heatmap-cell {
		aspect-ratio: 1;
		border-radius: 2px;
		cursor: pointer;
		transition: transform 0.15s ease, box-shadow 0.15s ease;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.heatmap-cell.empty {
		cursor: default;
	}

	.cell-date {
		font-size: 0.55rem;
		font-weight: 500;
		color: rgba(255, 255, 255, 0.7);
		line-height: 1;
		pointer-events: none;
	}

	.heatmap-cell:hover:not(.out-of-range):not(.empty) {
		transform: scale(1.15);
		box-shadow: 0 0 6px rgba(67, 97, 238, 0.4);
		z-index: 1;
	}

	.heatmap-cell.out-of-range {
		cursor: default;
		opacity: 0.2;
	}

	.heatmap-cell.out-of-range .cell-date {
		opacity: 0.5;
	}

	.heatmap-tooltip {
		position: absolute;
		transform: translate(-50%, -100%);
		background: var(--color-surface-2);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-sm);
		padding: 0.4rem 0.6rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.15rem;
		pointer-events: none;
		z-index: 10;
		white-space: nowrap;
	}

	.tooltip-date {
		font-size: 0.7rem;
		color: var(--color-text-muted);
	}

	.tooltip-amount {
		font-size: 0.8rem;
		font-weight: 600;
		color: var(--color-text);
	}

	.heatmap-legend {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.4rem;
		margin-top: 0;
	}

	.legend-label {
		font-size: 0.7rem;
		color: var(--color-text-muted);
	}

	.legend-scale {
		display: flex;
		gap: 2px;
	}

	.legend-cell {
		width: 12px;
		height: 12px;
		border-radius: 2px;
	}

	/* Loading skeletons */
	.chart-loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 1rem;
		padding: 2rem 0;
	}

	.loading-text {
		font-size: 0.85rem;
		color: var(--color-text-muted);
		animation: pulse 1.5s ease-in-out infinite;
	}

	.skeleton-donut {
		width: 200px;
		height: 200px;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.skeleton-ring {
		width: 160px;
		height: 160px;
		border-radius: 50%;
		border: 24px solid var(--color-surface-2);
		animation: pulse 1.5s ease-in-out infinite;
	}

	.skeleton-grid {
		display: flex;
		flex-direction: column;
		gap: 2px;
		width: 100%;
	}

	.skeleton-row {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 2px;
	}

	.skeleton-cell {
		aspect-ratio: 1;
		border-radius: 2px;
		background: var(--color-surface-2);
		animation: pulse 1.5s ease-in-out infinite;
	}

	@keyframes pulse {
		0%, 100% { opacity: 0.4; }
		50% { opacity: 0.8; }
	}

	/* Merchants */
	.merchants {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.merchant-row {
		display: flex;
		align-items: center;
		gap: 1rem;
		padding: 0.75rem 1rem;
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
		transition: border-color 0.2s ease, transform 0.2s ease;
	}

	.merchant-row:hover {
		border-color: var(--color-accent);
		transform: translateX(3px);
	}

	.merchant-name {
		flex: 1;
		font-size: 0.9rem;
	}

	.merchant-count {
		font-size: 0.8rem;
		color: var(--color-text-muted);
	}

	.merchant-total {
		font-size: 0.9rem;
		font-weight: 600;
	}

	/* Insights */
	.insights {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.insights li {
		padding: 0.75rem 1rem;
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		border-left: 3px solid var(--color-accent);
		font-size: 0.9rem;
		line-height: 1.5;
		transition: transform 0.2s ease, background 0.2s ease;
	}

	.insights li:hover {
		transform: translateX(3px);
		background: var(--color-surface-2);
	}

	/* Sources */
	.sources {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.source-item {
		padding: 0.5rem 1rem;
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
		font-size: 0.85rem;
	}

	.source-item a {
		color: var(--color-accent);
		text-decoration: none;
	}

	.source-item a:hover {
		text-decoration: underline;
	}

	.source-domain {
		color: var(--color-text-muted);
		font-size: 0.75rem;
		margin-left: 0.5rem;
	}

	.search-entry-point {
		padding: 0.75rem 1rem;
		background: var(--color-surface);
		border-radius: var(--radius-sm);
		border: 1px solid var(--color-border);
	}
</style>

<script lang="ts">
import { onMount } from 'svelte';
import { backend } from '$lib/canisters';
import { _ } from 'svelte-i18n';

let balance = 0;
let transactions: any[] = [];
let vaultStatus: any = null;
let loading = false;
let error = '';
let transferAmount = 0;
let transferTo = '';
let activeTab: 'balance' | 'transactions' | 'transfer' | 'admin' = 'balance';

async function loadBalance() {
loading = true;
error = '';
try {
const result = await backend.extension_call('vault', 'get_balance', JSON.stringify({
principal_id: (await backend.whoami()).toText()
}));
const data = JSON.parse(result);
if (data.success && data.data?.Balance) {
balance = data.data.Balance.amount || 0;
}
} catch (e: any) {
error = e.message || 'Failed to load balance';
} finally {
loading = false;
}
}

async function loadTransactions() {
loading = true;
error = '';
try {
const result = await backend.extension_call('vault', 'get_transactions', JSON.stringify({
principal_id: (await backend.whoami()).toText()
}));
const data = JSON.parse(result);
if (data.success && data.data?.Transactions) {
transactions = data.data.Transactions || [];
}
} catch (e: any) {
error = e.message || 'Failed to load transactions';
} finally {
loading = false;
}
}

async function loadStatus() {
loading = true;
error = '';
try {
const result = await backend.extension_call('vault', 'get_status', JSON.stringify({}));
const data = JSON.parse(result);
if (data.success && data.data?.Stats) {
vaultStatus = data.data.Stats;
}
} catch (e: any) {
error = e.message || 'Failed to load status';
} finally {
loading = false;
}
}

async function refreshVault() {
loading = true;
error = '';
try {
const result = await backend.extension_call('vault', 'refresh', JSON.stringify({}));
const data = JSON.parse(result);
if (data.success) {
await loadBalance();
await loadTransactions();
} else {
error = data.error || 'Refresh failed';
}
} catch (e: any) {
error = e.message || 'Failed to refresh vault';
} finally {
loading = false;
}
}

async function performTransfer() {
if (!transferTo || transferAmount <= 0) {
error = 'Please enter valid recipient and amount';
return;
}

loading = true;
error = '';
try {
const result = await backend.extension_call('vault', 'transfer', JSON.stringify({
to_principal: transferTo,
amount: transferAmount
}));
const data = JSON.parse(result);
if (data.success) {
transferTo = '';
transferAmount = 0;
await loadBalance();
await loadTransactions();
} else {
error = data.error || 'Transfer failed';
}
} catch (e: any) {
error = e.message || 'Failed to perform transfer';
} finally {
loading = false;
}
}

onMount(async () => {
await loadBalance();
await loadTransactions();
await loadStatus();
});
</script>

<div class="p-6 space-y-6">
<div class="flex justify-between items-center">
<h1 class="text-3xl font-bold">{$_('extensions.vault.title')}</h1>
<button
on:click={refreshVault}
disabled={loading}
class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
>
{loading ? 'Refreshing...' : 'Refresh'}
</button>
</div>

{#if error}
<div class="p-4 bg-red-50 border border-red-200 rounded text-red-800">
{error}
</div>
{/if}

<!-- Tabs -->
<div class="flex space-x-4 border-b">
<button
on:click={() => activeTab = 'balance'}
class="px-4 py-2 {activeTab === 'balance' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'}"
>
Balance
</button>
<button
on:click={() => activeTab = 'transactions'}
class="px-4 py-2 {activeTab === 'transactions' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'}"
>
Transactions
</button>
<button
on:click={() => activeTab = 'transfer'}
class="px-4 py-2 {activeTab === 'transfer' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'}"
>
Transfer
</button>
<button
on:click={() => activeTab = 'admin'}
class="px-4 py-2 {activeTab === 'admin' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-600'}"
>
Admin
</button>
</div>

<!-- Tab Content -->
<div class="mt-6">
{#if activeTab === 'balance'}
<div class="bg-white rounded-lg shadow p-6">
<h2 class="text-xl font-semibold mb-4">Your Balance</h2>
<div class="text-4xl font-bold text-blue-600">
{balance.toLocaleString()} satoshis
</div>
<div class="text-gray-600 mt-2">
≈ {(balance / 100000000).toFixed(8)} ckBTC
</div>
</div>
{:else if activeTab === 'transactions'}
<div class="bg-white rounded-lg shadow overflow-hidden">
<h2 class="text-xl font-semibold p-6 border-b">Transaction History</h2>
<div class="overflow-x-auto">
<table class="w-full">
<thead class="bg-gray-50">
<tr>
<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">From</th>
<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">To</th>
<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
</tr>
</thead>
<tbody class="divide-y divide-gray-200">
{#each transactions as tx}
<tr>
<td class="px-6 py-4 text-sm">{tx.id}</td>
<td class="px-6 py-4 text-sm font-mono text-xs">{tx.principal_from.substring(0, 20)}...</td>
<td class="px-6 py-4 text-sm font-mono text-xs">{tx.principal_to.substring(0, 20)}...</td>
<td class="px-6 py-4 text-sm">{tx.amount.toLocaleString()}</td>
<td class="px-6 py-4 text-sm"><span class="px-2 py-1 bg-blue-100 text-blue-800 rounded">{tx.kind}</span></td>
</tr>
{:else}
<tr>
<td colspan="5" class="px-6 py-4 text-center text-gray-500">No transactions found</td>
</tr>
{/each}
</tbody>
</table>
</div>
</div>
{:else if activeTab === 'transfer'}
<div class="bg-white rounded-lg shadow p-6">
<h2 class="text-xl font-semibold mb-4">Transfer Tokens (Admin Only)</h2>
<div class="space-y-4">
<div>
<label class="block text-sm font-medium text-gray-700 mb-2">
Recipient Principal
</label>
<input
type="text"
bind:value={transferTo}
placeholder="xxxxx-xxxxx-xxxxx-xxxxx-xxx"
class="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
/>
</div>
<div>
<label class="block text-sm font-medium text-gray-700 mb-2">
Amount (satoshis)
</label>
<input
type="number"
bind:value={transferAmount}
placeholder="100000000"
class="w-full px-4 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500"
/>
</div>
<button
on:click={performTransfer}
disabled={loading || !transferTo || transferAmount <= 0}
class="w-full px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
>
{loading ? 'Processing...' : 'Transfer'}
</button>
</div>
</div>
{:else if activeTab === 'admin'}
<div class="bg-white rounded-lg shadow p-6">
<h2 class="text-xl font-semibold mb-4">Vault Status</h2>
{#if vaultStatus}
<div class="space-y-4">
<div>
<h3 class="font-semibold text-gray-700">Application Data</h3>
<pre class="mt-2 p-4 bg-gray-50 rounded overflow-auto text-sm">{JSON.stringify(vaultStatus.app_data, null, 2)}</pre>
</div>
<div>
<h3 class="font-semibold text-gray-700">All Balances ({vaultStatus.balances?.length || 0})</h3>
<div class="mt-2 space-y-2">
{#each (vaultStatus.balances || []) as bal}
<div class="p-3 bg-gray-50 rounded">
<div class="font-mono text-xs">{bal.principal_id}</div>
<div class="text-sm font-semibold">{bal.amount.toLocaleString()} satoshis</div>
</div>
{/each}
</div>
</div>
</div>
{:else}
<p class="text-gray-500">Loading status...</p>
{/if}
</div>
{/if}
</div>
</div>

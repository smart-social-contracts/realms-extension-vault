<script lang="ts">
import { onMount } from 'svelte';
import { backend } from '$lib/canisters';
import { _ } from 'svelte-i18n';

let balance = 0;
let balanceObject: any = null;
let allBalances: any[] = [];
let transactions: any[] = [];
let vaultStatus: any = null;
let loading = false;
let error = '';
let transferAmount = 0;
let transferTo = '';
let activeTab: 'balance' | 'transactions' | 'transfer' | 'admin' = 'balance';
let currentPrincipal: string = '';
let canisterPrincipal: string = '';
let balancePagination: any = null;
let transferPagination: any = null;

async function loadBalance() {
loading = true;
error = '';
try {
// Get current user's principal
if (!currentPrincipal) {
currentPrincipal = await backend.get_my_principal();
}

// Fetch all Balance objects using get_objects_paginated
const response = await backend.get_objects_paginated('Balance', 0n, 100n);

if (response.success && response.data?.objectsListPaginated) {
const objectsData = response.data.objectsListPaginated;
balancePagination = objectsData.pagination;

// Parse each JSON string in the objects array
allBalances = objectsData.objects.map((objStr: string) => JSON.parse(objStr));

// Find the balance for the current user
balanceObject = allBalances.find(b => b.id === currentPrincipal || b._id === currentPrincipal);
balance = balanceObject ? (balanceObject.amount || 0) : 0;
} else {
balance = 0;
balanceObject = null;
}
} catch (e: any) {
console.error('Failed to load balance:', e);
error = e.message || 'Failed to load balance';
} finally {
loading = false;
}
}

async function loadTransactions() {
loading = true;
error = '';
try {
// Get canister principal (the vault backend canister ID)
if (!canisterPrincipal) {
// The canister ID is available from the backend module
// For now, we'll show all transfers since they're all vault-related
canisterPrincipal = 'vault'; // Placeholder - will be updated when we call backend
}

// Fetch all Transfer objects using get_objects_paginated
const response = await backend.get_objects_paginated('Transfer', 0n, 100n);

if (response.success && response.data?.objectsListPaginated) {
const objectsData = response.data.objectsListPaginated;
transferPagination = objectsData.pagination;

// Parse each JSON string in the objects array
// Show ALL transfers since the vault tracks all transactions to/from the canister
transactions = objectsData.objects.map((objStr: string) => JSON.parse(objStr));
} else {
transactions = [];
}
} catch (e: any) {
console.error('Failed to load transactions:', e);
error = e.message || 'Failed to load transactions';
} finally {
loading = false;
}
}

async function refreshVault() {
loading = true;
error = '';
try {
// Use extension_async_call for the refresh action
const result = await backend.extension_async_call({
extension_name: 'vault',
function_name: 'refresh',
args: '{}'
});

if (result.success) {
// Reload data after successful refresh
await loadBalance();
await loadTransactions();
} else {
error = result.response || 'Refresh failed';
}
} catch (e: any) {
console.error('Failed to refresh vault:', e);
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
// Use extension_async_call for the transfer action
const result = await backend.extension_async_call({
extension_name: 'vault',
function_name: 'transfer',
args: JSON.stringify({
to_principal: transferTo,
amount: transferAmount
})
});

if (result.success) {
transferTo = '';
transferAmount = 0;
await loadBalance();
await loadTransactions();
} else {
error = result.response || 'Transfer failed';
}
} catch (e: any) {
console.error('Failed to perform transfer:', e);
error = e.message || 'Failed to perform transfer';
} finally {
loading = false;
}
}

onMount(async () => {
await loadBalance();
await loadTransactions();
});
</script>

<div class="p-6 space-y-6 mb-64">
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
{#if balanceObject}
<div class="mt-4 p-4 bg-gray-50 rounded">
<p class="text-sm text-gray-600"><span class="font-medium">Principal:</span> <span class="font-mono text-xs">{balanceObject._id || balanceObject.id}</span></p>
</div>
{/if}
{#if balancePagination}
<div class="mt-3 text-xs text-gray-500">
Showing {allBalances.length} balance(s) (Page {Number(balancePagination.page_num) + 1} of {balancePagination.total_pages})
</div>
{/if}
</div>
{:else if activeTab === 'transactions'}
<div class="bg-white rounded-lg shadow overflow-hidden">
<h2 class="text-xl font-semibold p-6 border-b">Vault Transaction History</h2>
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
<td class="px-6 py-4 text-sm">{tx._id || tx.id}</td>
<td class="px-6 py-4 text-sm font-mono text-xs">{(tx.principal_from || '').substring(0, 20)}...</td>
<td class="px-6 py-4 text-sm font-mono text-xs">{(tx.principal_to || '').substring(0, 20)}...</td>
<td class="px-6 py-4 text-sm">{(tx.amount || 0).toLocaleString()}</td>
<td class="px-6 py-4 text-sm"><span class="px-2 py-1 bg-blue-100 text-blue-800 rounded">transfer</span></td>
</tr>
{:else}
<tr>
<td colspan="5" class="px-6 py-4 text-center text-gray-500">No transactions found</td>
</tr>
{/each}
</tbody>
</table>
</div>
{#if transferPagination}
<div class="p-4 border-t text-xs text-gray-500">
Showing all {transactions.length} vault transfer(s) (Total: {transferPagination.total_items_count} transfers in system)
</div>
{/if}
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
<h2 class="text-xl font-semibold mb-4">Vault Admin</h2>
<div class="space-y-4">
<div>
<h3 class="font-semibold text-gray-700">All Balances in System ({allBalances.length})</h3>
{#if allBalances.length > 0}
<div class="mt-2 space-y-2">
{#each allBalances as bal}
<div class="p-3 bg-gray-50 rounded">
<div class="font-mono text-xs mb-1">{bal._id || bal.id}</div>
<div class="text-sm font-semibold">{(bal.amount || 0).toLocaleString()} satoshis</div>
{#if bal.user}
<div class="text-xs text-gray-500 mt-1">User: {bal.user}</div>
{/if}
</div>
{/each}
</div>
{:else}
<p class="text-gray-500 mt-2">No balances found in system</p>
{/if}
</div>
<div class="mt-6">
<h3 class="font-semibold text-gray-700">All Transfers in System</h3>
{#if transferPagination}
<p class="text-sm text-gray-600 mt-2">Total transfers: {transferPagination.total_items_count}</p>
{:else}
<p class="text-gray-500 mt-2">No transfer data available</p>
{/if}
</div>
</div>
</div>
{/if}
</div>
</div>

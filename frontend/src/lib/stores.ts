import { writable } from 'svelte/store';

export const authenticated = writable<boolean>(false);
export const members = writable<any[]>([]);
export const loading = writable<boolean>(false);

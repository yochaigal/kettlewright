// Cairn for the JS tests: its manifest as the server gives it (generated from system/cairn; test_kettlewright.py
// checks it is current). The engine has no system of its own, so tests that play Cairn import this first.
import {readFileSync} from 'node:fs';
import {useSystem} from '#kettlewright';

export const CAIRN = JSON.parse(readFileSync(new URL('./cairn-system.json', import.meta.url)));
useSystem(CAIRN);

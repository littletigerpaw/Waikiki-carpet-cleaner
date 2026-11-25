import type { Role } from './types'

/** Where each role lands after logging in. */
export const homePathFor = (role: Role) => (role === 'manager' ? '/manager' : '/employee')

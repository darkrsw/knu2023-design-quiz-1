
import time

import lokisnbot
from . import pgsql
from .constants import *

def lsr(h, testnet=False):
    if testnet:
        return 100
    else:
        return 15000

def reward(h):
    return 16.5
    #return 14 + 50 * 2**(-h/64800)

base32z_dict = 'ybndrfg8ejkmcpqxot1uwisza345h769'

class ServiceNode:
    _data = None
    _state = None
    testnet = False
    def __init__(self, data=None, snid=None, pubkey=None, uid=None):
        """
        Constructs a ServiceNode object.  Can take a data dict (which typically contains all the
        fields fetched from a row of the service_nodes table, but must contain at least pubkey), or
        a (pubkey or snid) + uid pair to do the query during construction.
        """
        if data:
            if 'pubkey' not in data:
                raise RuntimeError("Given service node data is invalid")
            self._data = dict(data)
        elif uid and (snid or pubkey):
            cur = pgsql.dict_cursor()
            key = 'id' if snid else 'pubkey'
            cur.execute('SELECT * FROM service_nodes WHERE ' + key + ' = %s AND uid = %s', (snid or pubkey, uid))
            data = cur.fetchone()
            if data:
                self._data = dict(data)
            else:
                raise ValueError("Given SN " + key + " is unknown/invalid")
        else:
            raise RuntimeError("Invalid arguments: either 'data' or 'pubkey'/'uid' arguments must be supplied")

        try:
            self._state = lokisnbot.sn_states[self._data['pubkey']]
        except KeyError:
            try:
                self._state = lokisnbot.testnet_sn_states[self._data['pubkey']]
                self.testnet = True
            except KeyError:
                self._state = None

        if all(x in self._data for x in ('testnet', 'id', 'uid')) and self._state and self.testnet != self._data['testnet']:
            pgsql.cursor().execute("UPDATE service_nodes SET testnet = %s WHERE id = %s AND uid = %s",
                    (self.testnet, self._data['id'], self._data['uid']))

    @staticmethod
    def all(uid, sortkey=lambda sn: (sn['testnet'], sn['alias'] is None, sn['alias'] or sn['pubkey'])):
        cur = pgsql.dict_cursor()
        cur.execute("SELECT * FROM service_nodes WHERE uid = %s", (uid,))
        sns = []
        for row in cur:
            sns.append(ServiceNode(row))
        if sortkey:
            sns.sort(key=sortkey)
        return sns


    @staticmethod
    def pubkey_from_alias(uid, alias):
        cur = pgsql.dict_cursor()
        cur.execute("SELECT pubkey FROM service_nodes WHERE uid = %s AND alias = %s", (uid,alias))
        data = cur.fetchone()
        return data[0] if data else None


    def __getitem__(self, key):
        return self._data[key]


    def __contains__(self, key):
        return key in self._data


    def active(self):
        """Returns true if this is a known SN on either mainnet or testnet"""
        return self._state is not None

    def staked(self):
        """Returns true if this SN is fully staked and active"""
        return self.active() and self._state['total_contributed'] >= self._state['staking_requirement']

    def solo(self):
        """Returns true if this is a solo node"""
        return self._state['total_contributed'] >= self._state['staking_requirement'] and len(self._state['contributors']) == 1


    def active_on_network(self):
        """Returns true if this SN is currently active (i.e. staked and (if daemon is v4+) not decommissioned)"""
        return self.staked() and ('active' not in self._state or self._state['active'])


    def decommissioned(self):
        """Returns true if this SN is decommissioned.  Always returns false before v4."""
        return self.staked() and not self.active_on_network()


    def state(self, key):
        return self._state[key] if self._state and key in self._state else None


    def stored(self):
        """Returns whether this SN is stored in the database (technically, whether it has an id)"""
        return bool('id' in self._data and self._data['id'])


    def update(self, **kwargs):
        """Updates one or more keys in the database for this SN record.  This object's data gets
        updated to whatever actually gets stored in the database (i.e. incorporating any
        database-side conversions)"""

        if any(x not in self._data for x in ('id', 'uid')):
            raise RuntimeError('Unable to update an non-stored service node record')
        if 'id' in kwargs:
            raise RuntimeError("Can't update internal id!")
        keys, vals = [], []
        for k, v in kwargs.items():
            keys.append(k)
            vals.append(v)
        vals += (self._data['id'], self._data['uid'])
        cur = pgsql.dict_cursor()
        cur.execute("UPDATE service_nodes SET " + ", ".join(k + " = %s" for k in keys) + " WHERE id = %s AND uid = %s" +
                " RETURNING " + ", ".join(keys), tuple(vals))

        self._data.update(cur.fetchone())


    def delete(self):
        """Removes this SN from the database.  This object remains intact, but the `id` value will
        be deleted"""
        if any(x not in self._data for x in ('id', 'uid')):
            raise RuntimeError('Unable to delete an non-stored service node record')
        pgsql.cursor().execute("DELETE FROM service_nodes WHERE id = %s AND uid = %s", (self._data['id'], self._data['uid']))
        del self._data['id']


    def insert(self, exclude=set()):
        """Creates a new SN record in the database for this SN.  The SN must have been created with
        data elements that include only database columns or else excluded via the `exclude`
        argument.  After the insertion all values will be update to the just-inserted values as
        stored in the database (i.e. incorporating any database-level conversions or defaults)"""
        if 'id' in self._data:
            raise RuntimeError("SN is already stored")
        if 'uid' not in self._data or 'pubkey' not in self._data:
            raise RuntimeError("Cannot insert a SN row without a uid and pubkey")
        cols, vals = [], []
        for c, v in self._data.items():
            if c in exclude:
                continue
            cols.append(c)
            vals.append(v)
        cols = ', '.join(cols)
        vals = tuple(vals)
        cur = pgsql.dict_cursor()
        cur.execute("INSERT INTO service_nodes ("+cols+") VALUES %s RETURNING *", (vals,))
        self._data.update(cur.fetchone())


    def shortpub(self):
        return self._data['pubkey'][0:6] + '…' + self._data['pubkey'][-3:]


    def alias(self):
        """Returns sn['alias'], if set, otherwise a ellipsized version of the pubkey"""
        return ('alias' in self._data and self._data['alias']) or self.shortpub()


    def operator_fee(self):
        """Returns the operator fee as a portion (NOT a percentage), e.g. returns 0.02 for a 2% fee.
        Returns None if this is not an active SN.  Note that solo nodes have a fee of 100%"""
        return self._state['portions_for_operator'] / 18446744073709551612. if self.active() else None


    def lokinet_snode_addr(self):
        """Returns the lokinet snode address"""
        if 'pubkey_ed25519' not in self._state:
            return None
        pk_hex = self._state['pubkey_ed25519']
        if not pk_hex or len(pk_hex) != 64:
            return None
        bits = 0
        val = 0
        result = ''
        for x in pk_hex:
            bits += 4
            val = (val << 4) + int(x, 16)
            if bits >= 5:
                bits -= 5
                v = val >> bits
                val &= (1 << bits) - 1
                result += base32z_dict[v]
        result += base32z_dict[val << (5 - bits)]
        return result + ".snode"


    def proof_age(self):
        lup = None
        if 'last_uptime_proof' in self._state:
            lup = self._state['last_uptime_proof']
        if not lup:
            return None
        return int(time.time() - lup)


    def format_proof_age(self, extra_short=False):
        ago = self.proof_age()
        if ago is None:
            return '_No proof received_'
        seconds = ago % 60
        minutes = (ago // 60) % 60
        hours = (ago // 3600)
        return ('_No proof received_' if ago is None else
                (
                    (   '{}h{:02d}m'.format(hours, minutes) if hours else
                        '{}m'.format(minutes) if minutes else
                        '{}s'.format(seconds)
                    ) if extra_short else (
                        '{}h{:02d}m{:02d}s'.format(hours, minutes, seconds) if hours else
                        '{}m{:02d}s'.format(minutes, seconds) if minutes else
                        '{}s'.format(seconds)
                    )
                ) + ' ago' + (' ⚠' if ago >= PROOF_AGE_WARNING else '')
                )


    def lokinet_unreachable(self):
        """Returns None if lokinet is currently marked as reachable, the last reached timestamp if
        unreachable (or 0 if never reachable)."""
        if 'lokinet_reachable' not in self._state or self._state['lokinet_reachable']:
            return None

        return self._state['lokinet_first_unreachable']


    def ss_unreachable(self):
        """Same as above, but for storage server"""
        if 'storage_server_reachable' not in self._state or self._state['storage_server_reachable']:
            return None

        return self._state['storage_server_first_unreachable']


    def decomm_credit_blocks(self):
        """Returns the number of blocks of decomm credit remaining (if decommissioned) or available for decomm (if active)."""
        blocks = None
        if 'earned_downtime_blocks' in self._state:
            blocks = self._state['earned_downtime_blocks']
        if blocks and blocks >= 0:
            return blocks
        return None


    def format_decomm_credit(self):
        blocks = self.decomm_credit_blocks()
        if not blocks:
            return '*NONE*'
        seconds = blocks * AVERAGE_BLOCK_SECONDS
        return '*{}* blocks (about '.format(blocks) + (
                '{:.1f} hours'.format(seconds / 3600) if seconds > 90*60 else
                '{:.0f} minutes'.format(seconds / 60)
                ) + ')'


    @staticmethod
    def to_version_string(snv):
        """Takes a list like [1,2,3] and returns a string like "1.2.3" """

        ver = None
        # 3.0.x fakes its version as 2.3.x before the v11 fork to keep 2.0.x happy (which has a
        # bug requiring major version == 2 for v10 network uptime proofs), so un-fake it:
        if snv and snv != [0, 0, 0]:
            if len(snv) == 3 and snv[0] == 2 and snv[1] == 3:
                ver = "3.0.{}".format(snv[2])
            else:
                ver = ".".join("{}".format(x) for x in snv)
        return ver


    def version(self):
        """Return the version string of the service node, typically as a 3-element list, or None if
        not available.  (Requires a patched lokid that adds this info)"""
        return self._state['service_node_version'] if 'service_node_version' in self._state else None


    def version_str(self):
        return ServiceNode.to_version_string(self.version())


    def moon_symbol(self, pct=None):
        if pct is None:
            pct = 0
            if self._state:
                pct = self._state['total_contributed'] / self._state['staking_requirement'] * 100
        return '🌑' if pct < 26 else '🌒' if pct < 50 else '🌓' if pct < 75 else '🌔' if pct < 100 else '🌕'


    def infinite_stake(self):
        """Returns true if this SN was registered with an infinite stake (whether or not that stake is currently set to expire)."""
        if not self.active():
            return None;
        return self._state['registration_height'] >= (TESTNET_INFINITE_FROM if self.testnet else INFINITE_FROM)


    def expiry_block(self):
        """Returns the block when this SN expires, or None if it isn't registered or doesn't expire"""
        if not self.active():
            return None
        if self.infinite_stake():
            return self._state['requested_unlock_height'] or None
        else:
            return self._state['registration_height'] + (TESTNET_STAKE_BLOCKS if self.testnet else STAKE_BLOCKS)


    def expires_in(self):
        """Returns the estimate of the time until the stake expires, in seconds.  Returns None if
        the SN is not registered or if the SN uses infinite staking (once supported)."""
        block = self.expiry_block()
        if not block:
            return None
        elif self.testnet:
            height = lokisnbot.testnet_network_info['height']
        else:
            height = lokisnbot.network_info['height']
        return (block - height + 1) * AVERAGE_BLOCK_SECONDS


    def expires_soon(self):
        ttl = self.expires_in()
        return ttl is not None and ttl < 3600 * max(
                lokisnbot.config.TESTNET_EXPIRY_THRESHOLDS if self.testnet else lokisnbot.config.EXPIRY_THRESHOLDS)


    def status_icon(self):
        status_icon, prefix = '🛑', ''
        if not self.active():
            return status_icon
        elif self.testnet:
            prefix = '🚧'

        proof_age = int(time.time() - self._state['last_uptime_proof'])
        if self.decommissioned():
            status_icon = '☣'
        elif proof_age >= PROOF_AGE_WARNING:
            status_icon = '⚠'
        elif self.lokinet_unreachable() is not None or self.ss_unreachable() is not None:
            status_icon = '⛔'
        elif ((lokisnbot.config.WARN_VERSION_LESS_THAN and self.version() < lokisnbot.config.WARN_VERSION_LESS_THAN)
                or (lokisnbot.config.LATEST_VERSION and self.version() < lokisnbot.config.LATEST_VERSION)):
            status_icon = '🔼'
        elif self._state['total_contributed'] < self._state['staking_requirement']:
            status_icon = self.moon_symbol()
        elif self.expires_soon():
            status_icon = '⏱'
        elif self.infinite_stake() and self.expiry_block():
            status_icon = '📆'
        else:
            status_icon = '💚'

        return prefix + status_icon


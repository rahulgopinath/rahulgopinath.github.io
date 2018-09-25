---
published: false
title: A self-learning proxy-network with Reinforment Learning
layout: post
comments: true
tags: proxy
---


## Some prerequisites

```python
import re, random
random.seed(0)
```

### An LRU cache

A proxy server needs to store the contents of the URLs that it fetched once (subject to some constraints). We use a simple LRU cache for that purpose.
```python
class Cache:
    def __init__(self, max_size=4):
        self._data, self._max_size = {}, max_size

    def __setitem__(self, key, value):
        self._data[key] = [0, value]
        self._age_keys()
        self._prune()

    def __getitem__(self, key):
        if key not in self._data: return None
        value = self._data[key]
        self._renew(key)
        self._age_keys()
        return value[1]

    def _renew(self, key): self._data[key][0] = 0

    def _delete_oldest(self):
        m = max(i[0] for i in self._data.values())
        self._data = {k:v for k,v in self._data.items() if v[0] == m}

    def _age_keys(self):
        for k in self._data: self._data[k][0] += 1

    def _prune(self):
        if len(self._data) > self._max_size: self._delete_oldest()
```

### The _Origin_ server

The proxy servers at the end forward a request to the corresponding origin servers. These servers (typically HTTP Servers) are identified by their domain and are responsible for processing the request, and crafting the appropriate response. Hence, here we simulate an origin serveer with a simple object that is responsible for a domain and contains a list of paths it can serve.

```python
class HTTPServer:
    def domain(self): return self._domain
    def __init__(self, domain, pages):
        self._domain = domain
        self._page = {path:HTTPResponse(domain,path, "< A page from %s/%s >"
            % (domain, path),{}) for path in pages}
    def get(self, path): return self._page[path]
```

#### The request

The supporting classes for _HTTPServer_. First is the _HTTPRequest_ which knows which _origin_ server can serve this request.

```python
class HTTPRequest:
    def __init__(self, domain, page):
        self._domain, self._page = domain, page
        self._url = 'http://%s/%s' % (domain, page)
    def domain(self): return self._domain
    def page(self): return self._page
    def header(self): return []
    def url(self): return self._url
```
#### The response
The response also does some work in propagating the _Q_ value and _Reward_.

```python
class HTTPResponse:
    def __init__(self, domain, url, content, header, status=200):
        self._page = {'domain': domain, 'url': url, 'content': content, 'header': header}
        self._status = status
        self._page['header']['Q'] = 0
    def __str__(self): return self._page['url']
    def set_reward(self, r): self._page['header']['QReward'] = str(r)
    def get_reward(self): return int(self._page['header']['QReward'])
    def get_q_header(self): return self._page['header']['Q']
    def set_q_header(self, value): self._page['header']['Q'] = value
    def status(self): return self._status

```

### The _Reward_ for different results.

We need to specify different rewards for different accomplishments. These values can be tuned to produce different learning rates.

```python
class Reward:
    def __init__(self, proxy): self._proxy = proxy
    def get_reward(self, status):
        # if we are not the end point, just return -1 * load
        # if we are, then return (100 - load)
        if status == 'MidWay': return -1
        if status == 'EndPoint': return 500
        if status == 'CacheHit': return 500
        if status == 'NoService': return -500
        assert False
```

### Q containers

Each proxy server maintains a list of upstream servers. It also maintains
a dynamic list of _Q_ values for each of those servers corresponding to the
_domain_ names of _URLs_ that it encounters. The decision to route a URL to
a particular proxy server is taken based on its _Q_ value for that domain.

```python
class Q:
    def __init__(self, parents):
        self._parents, self._q = list(parents.values()), {}

    def get_q(self, s_url_domain,a_parent):
        key = self.to_key(s_url_domain,a_parent)
        if key not in self._q:
            self._q[key] = 0
        return self._q[key]

    def put_q(self, s_url_domain, a_parent, value):
        key = self.to_key(s_url_domain,a_parent)
        self._q[key] = value

    def max_a(self,s_url_domain):
        # best next server for this state.
        srv = self._parents[0]
        maxq = self.get_q(s_url_domain, srv)
        for a_p in self._parents:
           q = self.get_q(s_url_domain, a_p)
           if q > maxq:
               maxq = q
               srv = a_p
        return srv

    def to_key(self, s_url_domain, a_parent):
        return 'url[%s]: parent[%d]' % (s_url_domain,a_parent.name())
```

### Our policy

The policy is essentially a mechanism to produce an action given a state.

```python
class Policy:
    def __init__(self, proxy, q): self._proxy, self._q = proxy, q
    def next(self, req): pass
    def update(self, domain,proxy,last_max_q, reward): pass
    def max_a_val(self, domain): pass

Alpha = 0.1 # Learning rate
Beta = 1    # Discounting factor

class QPolicy(Policy):
    def __init__(self, proxy, q):
        self._proxy = proxy
        self._alpha, self._beta = Alpha, Beta

        # Action is the next server to choose from
        self._q = q
        self._time_step = 0

    def q(self): return self._q

    def next(self, req):
        global g_path
        # GLIE - Greedy in the limit, with infinite exploration
        # slowly converge to pure greedy as time steps increase.
        # * If a state is visited infinitely often, then each action
        #   In that state is chosen infinitely often
        # * In the limit, the learning policy is greedy wrt the
        #   learned Q function with probability 1
        s = random.randint(0, self._time_step)
        self._time_step += 1
        if s == 0: # Exploration
            g_path.append('*')
            return random.choice(list(self._proxy._parents.values()))
        else: # Greedy
            proxy = self._q.max_a(req.domain())
            return proxy

    def max_a_val(self, s_url_domain):
        a_parent = self._q.max_a(s_url_domain)
        val = self._q.get_q(s_url_domain, a_parent)
        return val

    def update(self, s_url_domain, a_parent, last_max_q, reward):
        # Q(a,s)  = (1-alpha)*Q(a,s) + alpha(R(s) + beta*max_a(Q(a_,s_)))
        # the a is self here.
        q_now = self._q.get_q(s_url_domain, a_parent)
        q_new = (1 - self._alpha) * q_now + self._alpha*(reward + self._beta*last_max_q)
        self._q.put_q(s_url_domain, a_parent, q_new)
```

### The Proxy Node

Each proxy node maintains its own _q(s,a)_ value and each proxy is able to reach a fixed set of domains. for others, it has to rely on parents.

```python
class ProxyNode:
    def __init__(self, name, domains, parents):
        self._name = name
        self._parents = parents
        self._domains = domains
        self._q = Q(parents)
        self._policy = QPolicy(self, self._q)
        self._reward = Reward(self)
        self._cache = Cache()

    def policy(self): return self._policy

    def name(self): return self._name
    # use this proxy to send request.
    # it returns back a hashmap that contains the body of response
    # and a few headers.
    def request(self, req):
        global g_path, g_reward
        res = self._cache[req.url()]
        if res is not None:
            g_path.append(self._name)
            g_path.append("+")
            my_reward = self._reward.get_reward('CacheHit')
            res.set_reward_header(my_reward)
            g_reward.append(my_reward)
            return res
        res = self._request(req)
        if res.status() == 200:
            self._cache[req.url()] = res
        return res

    def is_edge(self): return My_Network.is_edge(self._name)

    def knows_origin(self, domain): return domain in self._domains

    def _request(self, req):
        global g_path, g_reward
        res = None
        g_path.append(self._name)
        # is this one of the domains we can serve?
        if self.knows_origin(req.domain()):
           res = self.fetch(req)
           my_reward = self._reward.get_reward('EndPoint')
           res.set_reward_header(my_reward)
           g_reward.append(my_reward)
           return res
        elif self.is_edge():
            res = HTTPResponse(req.domain(),req.url(),
                    "Can't service", {'last_proxy':  self._name}, 501)
            my_reward = self._reward.get_reward('NoService')
            res.set_reward_header(my_reward)
            g_reward.append(my_reward)
            return res
        else:
            res = self.forward(req)
            my_reward = self._reward.get_reward('MidWay')
            res.set_reward_header(my_reward)
            g_reward.append(my_reward)
            return res

    def fetch(self, req): return self._domains[req.domain()].get(req.page())

    def forward(self, req):
        #puts "req at #{self._name}"
        proxy = self._policy.next(req)
        res =  proxy.request(req)
        # updaate q
        last_max_q = int(res.get_q_header())

        reward = res.get_reward_header()
        self._policy.update(req.domain(),proxy,last_max_q, reward)

        # find the q value for the next best server for domain
        next_q = self._policy.max_a_val(req.domain())
        res.set_q_header(next_q)
        return res
```

### Network

Our proxy network. For ease of use, we initialize the links at once place.
In the real world, the network is formed as the proxy servers initialize
themselves with its parent and peer names. Further, the network would be a lot
more dynamic in the real world with proxies joining and departing the network.

```python

class Network:

    def __init__(self, lvl_const, num_origin, num_pages):
        self._lvl_const = lvl_const
        self._num_origin = num_origin
        self._num_pages = num_pages

        # The number of parent servers per proxy
        self._num_parents = 2
        # The average number of proxy servers at each level
        self.network_width = 10
        # The average number of hops for a request before reaching origin
        self.network_levels = 10

        # construct the initial topology
        self.servers = self.populate_origin_servers()
        self.proxies = self.populate_proxy_servers()
        self._db = {}
        for p in sorted(self.proxies.keys()):
            self.create_proxy(p, self.proxies[p])

    def proxy_name(self, lvl, rank): return lvl*self._lvl_const + rank
    # an edge proxy. That is, servers
    # with ids 101, 102 etc. where the origins are
    # 1,2,...
    def is_edge(self, i): return i <  self._lvl_const*2
    def parents(self,p_id,lvl,rank,network_width):
        """
        Identify two random proxy servers in the level up as the parents for
        each proxy server.
        """
        direct_parent = p_id - self._lvl_const
        parent_proxies = {direct_parent}
        for i in range(1,self._num_parents+1):
            another_rank = (rank + random.randint(0, self._num_parents-1)) % self.network_width + 1
            parent_proxies.add(self.proxy_name(lvl-1, another_rank))
        return list(parent_proxies)

    def populate_origin_servers(self):
        # construct the origin servers
        server = {}
        for i in range(1,self._num_origin+1):
            paths = ["path-%d/page.html" % page for page in range(1,self._num_pages+1)]
            server[i] = HTTPServer("domain%d.com" % i, paths)
        return server

    def populate_proxy_servers(self):
        proxies = {}

        for lvl in range(1,self.network_levels+1):
            for rank in range(1,self.network_width+1):
                p_id = self.proxy_name(lvl, rank)
                proxies[p_id] = self.parents(p_id,lvl,rank,network_width)
        return proxies

    def create_proxy(self, p, parents):
        if p not in self._db:
            if self.is_edge(p):
                domains = {p:self.servers[p] for p in parents}
                parents = {}
            else:
                domains = {}
                parents = {p:self._db[p] for p in parents}
            proxy = ProxyNode(p, domains, parents)
            self._db[p] = proxy
        return self._db[p]

    def user_req(self, req):
        proxy = self.proxy_name(self.network_levels, random.randint(1, self.network_width))
        return self._db[proxy].request(req)
```

### Simulation of the network traffic.

```python
g_path = []
g_reward = []
# LEVEL_CONST is the maximum number of proxy servers in a level, so that
# we can look at a proxy and determine which level it is.
Level_Const = 100
Num_Origin = 10
Num_Pages = 10

My_Network = Network(Level_Const, Num_Origin, Num_Pages)
iter_total = 100
max_count = 0
for i in range(iter_total):
    count = 0
    total = 100
    for j in range(1,total+1):
        page = "path-%s/page.html" % (random.randint(1,10))
        server_id = random.randint(1,10)
        req = HTTPRequest(server_id, page)
        res = My_Network.user_req(req)
        trejectory = ''.join([str(j) + '>' for j in g_path]) + \
              ("*" if res.status() == 200 else "X") + "  " + str(req.domain())
        print(trejectory)
        g_path = []
        g_reward = []
        if res.status() > 500: count += 1
    print("%d/%d" % (count,total))
    max_count = i
    if count == 0: break
print("maxcount: ",max_count)
```

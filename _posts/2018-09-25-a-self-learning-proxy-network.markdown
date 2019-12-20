---
published: true
title: A self-learning proxy-network with reinforment learning (Q-Learning)
layout: post
comments: true
tags: proxy
categories: post
---

In this post, I describe how to use _Q-learning_ within a caching proxy network so that the network learns the best route to use to fetch URLs from servers. For the purpose of this post, the proxy network and the origin servers are simulated.

Note that this is a rather simple implementation of a cache routing, and is not meant as a competitor to other cache routing protocols such as _[ICP](https://en.wikipedia.org/wiki/Internet_Cache_Protocol)_, _[HTCP](https://en.wikipedia.org/wiki/Hypertext_caching_protocol)_, _[CARP](https://en.wikipedia.org/wiki/Cache_Array_Routing_Protocol)_ etc. Specifically, we do not handle the cache discovery. Further, we have to resort to repeated requests if initial routing does not succeed (i.e. there is no guarantee like in CARP that a particular route will succeed). However, I believe that these deficiencies can be overcome if necessary.

One of the advantages we gain is that the proxy network is much more adaptive, and can dynamically reconfigure itself in response to changing resources. Further, simple modifications to the computation of _Q_ value can be used to implement load balancing between proxy servers.


## Reinforcement-learning overview

The idea of reinforcement learning is simple. We have an agent that tries to figure out how to behave in an environment (without preconceptions) such that it can maximize the rewards it can get from a that environment. The rewards are assigned based on what state the environment changed to as a result of the agents behavior. The actions of the agent are not guaranteed to produce a desired outcome, but rather have a high chance of producing specified state changes.

The agent typically tries to learn how to behave by producing random actions, and observing the effect of these actions on the environment.

### The balance between caution and risk-taking

While the agent can initially generate random actions, once any of these actions have resulted in a positive reward, the agent has a choice. The agent can continue making random choices, so that it can learn which other actions can result in (perhaps better) rewards or it can stick to the known action which produced a reward. The problem is how to balance between the conservative approach and risky exploration. Further, once the agent achieves some reward, it is often not clear which action was actually responsible for this reward. It may be that the change in environment was delayed, or perhaps multiple actions had an impact.

The question that we tackle is how to maximize the future rewards an agent might obtain from an environment (and hence take an action that leads to maximization of rewards). _Q-Learning_ is one of the formal solutions for this problem.

### Q-Learning

In _Q-Learning_, one tries to maximize the future rewards based on certain constraints. In particular, the immediate rewards are given more weight, while possible future rewards are discounted by a certain ratio. That is,

$$ R_{n} = r_0 \times \beta + r_1 \times \beta^2 + r_2 \times \beta^3 ... r_n \times \beta^n $$

Where $$ r_i$$ is the reward at step _i_ and $$\beta$$ is the discounting ratio for future rewards, and $$R_n$$ is the total reward after _n_ steps. We define a function _Q_ such that it represents the maximum possible future reward (discounted) for performing an action _a_ in state _s_.

$$ Q(a_i,s_i) = max R_{i+1} $$

This can be rewritten as

$$ Q(a,s) = r + \beta max_{a^{'}} Q(a^{'}, s^{'}) $$

That is, the optimal reward from performing some action _a_ at current state (resulting in _s'_) is the reward for action _a_ in this state in addition to performing optimally from the next step onwards. This equation is called the [Bellman equation](https://en.wikipedia.org/wiki/Bellman_equation). The interesting thing about Bellman equation is that it can be iteratively approximated, and this is what reinforcement learning is doing.

That is, we initialize all values of _Q(a,s)_ randomly, and then start with initial state _s_ and
iteratively perform actions on it and keep updating.

```
Q[a,s]  = (1-alpha)*Q[a,s] + alpha*(reward(s) + beta*max_a(Q(_,s_)))
```
Here, $$\alpha$$ is the learning rate.

### Q-Learning for proxy servers

The main intuition for using _Q-Learning_ for proxy servers is that each hop from one proxy to another can be considered to be an action, and the state is the state of the proxy server when it receives a URL to forward. The point here is that the hierarchy of proxy servers form the _Q_ table, with corresponding states and actions. The domain of the URLs received is considered here as a state, so that we have _Q(domain, parent_proxy)_ as the reward for choosing _parent_proxy_ for the particular URL. The nice thing here is that a proxy server need to only keep track of rewards for routing seen domains to its direct upstream proxy servers, and take care of updating the table when it gets responses for the routed requests.

##  The implementation

### Some prerequisites

```python
import re, random
random.seed(0)
```

### An LRU cache

A proxy server needs to store the contents of the URLs that it fetched once (subject to some constraints). We use a simple LRU cache for that purpose. We age all keys each time a response is inserted into the cache, and renew a key when ever there was a cache hit for that key. We also prune keys when the cache grows beyond a specified size (here _4_ items).

```python

class Cache:
    def __init__(self, max_size=4): self._data, self._max_size = {}, max_size

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

The _Origin_ servers are the servers that actually serve the URLs.

The proxy servers at the edge forwards a request to the corresponding origin servers. These servers (typically HTTP Servers) are identified by their domain and are responsible for processing the request, and crafting the appropriate response. Hence, here we simulate an origin server with a simple object that is responsible for a domain and contains a list of paths it can serve.

```python
class HTTPServer:
    def domain(self): return self._domain
    def __init__(self, domain, paths):
        self._domain = domain
        self._pages = {path:HTTPResponse(domain,path,
            "< A page from %s/%s >" % (domain, path),{}) for path in paths}
    def get(self, path): return self._pages[path]
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
    def header(self): return None
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
    def set_reward_header(self, r): self._page['header']['QReward'] = str(r)
    def get_reward_header(self): return int(self._page['header']['QReward'])
    def get_q_header(self): return self._page['header']['Q']
    def set_q_header(self, value): self._page['header']['Q'] = value
    def status(self): return self._status
```

### The _Reward_

We need to specify different rewards for different accomplishments. These values can be tuned to produce different learning rates.

```python
class Reward:
    MidWay = -1
    EndPoint = 500
    CacheHit = 500
    NoService = -500
```

### Q containers

Each proxy server maintains a list of upstream servers. It also maintains
a dynamic list of _Q_ values for each of those servers corresponding to the
_domain_ names of _URLs_ that it encounters. The decision to route a URL to
a particular proxy server is taken based on its _Q_ value for that domain.

```python
class Q:
    def __init__(self, parents): self.parents, self._q = parents, {}

    def __getitem__(self, val):
        key = self.to_key(val)
        if key not in self._q: self._q[key] = 0
        return self._q[key]

    def __setitem__(self, val, value): self._q[self.to_key(val)] = value

    def to_key(self, val): return 'domain[%s]: proxy[%d]' % val

    def explore(self): return random.choice(self.parents)

    def max_a(self,s_url_domain):
        # best next server for this state.
        srv = self.parents[0]
        maxq = self[(s_url_domain, srv)]
        for parent in self.parents:
           q = self[(s_url_domain, parent)]
           if q > maxq: maxq, srv = q, parent
        return srv
```

### The Policy

The policy is essentially a mechanism to produce an action given a state. Our policy is GLIE -- that is greedy in the limit with infinite exploration. It slowly converges to pure greedy choice as time steps increase. To qualify as GLIE, we need to fulfil the following conditions

* If a state is visited infinitely often, then each action in that state is chosen infinitely often
* In the limit, the learning policy is greedy with respect to the learned Q function with probability 1

```python
Alpha = 0.1 # Learning rate
Beta = 1    # Discounting factor

class QPolicy:
    def __init__(self, lst): self._q, self._time_step = Q(lst), 0

    def q(self): return self._q

    def next_hop(self, req):
        s = random.randint(0, self._time_step)
        self._time_step += 1
        if s == 0: return self._q.explore()
        else: return self._q.max_a(req.domain())

    def max_a_val(self, s_url_domain):
        a_parent = self._q.max_a(s_url_domain)
        return self._q[(s_url_domain, a_parent)]

    def update(self, s_url_domain, a_parent, last_max_q, reward):
        # Q(a,s)  = (1-alpha)*Q(a,s) + alpha(R(s) + beta*max_a(Q(a_,s_)))
        q_now = self._q[(s_url_domain, a_parent)]
        q_new = (1 - Alpha) * q_now + Alpha*(reward + Beta*last_max_q)
        self._q[(s_url_domain, a_parent)] = q_new
```

### The Proxy Node

Each proxy node maintains its own _q(domain,proxy)_ value table and each proxy is able to reach a fixed set of domains. for others, it has to rely on parents.

```python
class ProxyNode:
    def __init__(self, name, domains, parents):
        self._name, self._parents, self._domains = name, parents, domains
        self._policy = QPolicy(list(parents.keys()))
        self._reward = Reward()
        self._cache = Cache()

    # use this proxy to send request.
    # it returns back a hashmap that contains the body of response
    # and a few headers.
    def request(self, req):
        res = self._cache[req.url()]
        if res is not None:
            res.set_reward_header(self._reward.CacheHit)
            return res
        res = self._request(req)
        if res.status() == 200:
            self._cache[req.url()] = res
        return res

    def is_edge(self): return My_Network.is_edge(self._name)

    def knows_origin(self, domain): return domain in self._domains

    def fetch(self, req): return self._domains[req.domain()].get(req.page())

    def _request(self, req):
        # is this one of the domains we can serve?
        if self.knows_origin(req.domain()):
           res = self.fetch(req)
           res.set_reward_header(self._reward.EndPoint)
           return res
        elif self.is_edge():
            res = HTTPResponse(req.domain(),req.url(),
                    "Can't service", {'last_proxy':  self._name}, 501)
            res.set_reward_header(self._reward.NoService)
            return res
        else:
            res = self.forward(req)
            res.set_reward_header(self._reward.MidWay)
            return res

    def forward(self, req):
        proxy = self._policy.next_hop(req)
        res =  self._parents[proxy].request(req)
        # update q
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
    def __init__(self, lvl_const, num_origin, num_pages, num_parents, network_width, network_levels):
        # the maximum limit for network_width
        self._lvl_const = lvl_const
        # the numbeer of origin servers
        self._num_origin = num_origin
        # the number of pages per origin server
        self._num_pages = num_pages
        # The number of parent servers per proxy
        self._num_parents = num_parents
        # The average number of proxy servers at each level
        self.network_width = network_width
        # The average number of hops for a request before reaching origin
        self.network_levels = network_levels

        servers = self.populate_origin_servers()
        proxies = self.populate_proxy_servers() # keys are in insert order
        self._db = {}
        for p in proxies.keys(): self.create_proxy(p, proxies[p], servers)

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
            another_rank = (rank + random.randint(0, self._num_parents-1)) % network_width + 1
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
                proxies[p_id] = self.parents(p_id,lvl,rank,self.network_width)
        return proxies

    def create_proxy(self, p, parents, servers):
        if p not in self._db:
            if self.is_edge(p):
                domains, parents = {p:servers[p] for p in parents}, {}
            else:
                domains, parents = {}, {p:self._db[p] for p in parents}
            proxy = ProxyNode(p, domains, parents)
            self._db[p] = proxy
        return self._db[p]

    def user_req(self, req):
        proxy = self.proxy_name(self.network_levels,
                random.randint(1, self.network_width))
        # print("req starting at %s for %s" % (proxy, req.domain()))
        # print(req.url())
        res = self._db[proxy].request(req)
        return res
```

### Simulation of the network traffic.

* _Level_Const_ is the maximum number of proxy servers in a level, so that we can look at a proxy and determine which level it is.
* _Num_Pages_ is the number of pages each HTTP server holds
* _Num_Parents_ is the number of parent proxies that each downstream proxy is linked to
* _Network_Width_ is the number of peers a  proxy server has. (Limited by the _Level_Const_)
* _Network_Levels_ is the maximum number of hops that a request has to travel in the network.

```python
My_Network = Network(100, 10, 10, 2, 10, 10)
iter_total, total = 100, 100
max_count = 0
for i in range(iter_total):
    count = 0
    for j in range(total):
        page = "path-%s/page.html" % (random.randint(1,10))
        server_id = random.randint(1,10)
        req = HTTPRequest(server_id, page)
        res = My_Network.user_req(req)
        if res.status() > 500: count += 1
    print("%d/%d" % (count,total))
    max_count = i
    if count == 0: break
print("maxcount: ",max_count)
```

## Running the experiment

```bash
$ python3 network.py 
58/100
29/100
19/100
14/100
11/100
1/100
1/100
2/100
1/100
2/100
0/100
maxcount:  10
```

{% gist 4cb7acda57c49ca3a1c7c9cc834cc8a7 %}

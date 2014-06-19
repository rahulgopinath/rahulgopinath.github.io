---
layout: page
title: Rahul Gopinath
tagline: .
---
{% include JB/setup %}

Rahul is a PhD candidate in *Software Testing*, specializing in *Mutation Analysis*. His interests include Programming Languages, Statistics, and Logic.

Supervisor: Dr. Carlos Jensen  
Research Team: HCI  


## Posts

<ul class="posts">
  {% for post in site.posts %}
    {% if post.tags contains 'ta' %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
    {% else %}
    <hr>
    {{post.tags | join ','}}
    <hr>
    {% endif %}
  {% endfor %}
</ul>

<p/>
---
<p/>
<p/>

<a class="twitter-timeline" href="https://twitter.com/_rahulgopinath" data-widget-id="479223024294457344">Tweets by @_rahulgopinath</a>
<script>!function(d,s,id){var js,fjs=d.getElementsByTagName(s)[0],p=/^http:/.test(d.location)?'http':'https';if(!d.getElementById(id)){js=d.createElement(s);js.id=id;js.src=p+"://platform.twitter.com/widgets.js";fjs.parentNode.insertBefore(js,fjs);}}(document,"script","twitter-wjs");</script>


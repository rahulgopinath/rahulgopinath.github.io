---
layout: page
title: Rahul Gopinath
tagline: .
---
{% include JB/setup %}

Rahul is a PhD candidate in <i>Software Testing</i>, specializing in <i>Mutation Analysis</i>. His interests include Programming Languages, Statistics, and Logic.<p/>

Supervisor: Dr. Carlos Jensen<br/>
Research Team: HCI<br/>


## Posts

<ul class="posts">
  {% for post in site.posts %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>


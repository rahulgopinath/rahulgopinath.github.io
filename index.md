---
layout: page
title: Rahul Gopinath
tagline: .
---
{% include JB/setup %}

Rahul is a PhD candidate in <i>Software Testing</i>, specializing in <i>Mutation Analysis</i>. However, his interests range from Programming Languages, Statistics, and Logic.

Supervisor: Dr. Carlos Jensen
Research Team: HCI


## Posts

<ul class="posts">
  {% for post in site.posts %}
    <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url }}">{{ post.title }}</a></li>
  {% endfor %}
</ul>


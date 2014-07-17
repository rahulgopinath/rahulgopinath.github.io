---
layout: page
title : Posts
header : Posts
group: navigation
weight: 3
menu: Posts
---


<h3> Writing a language </h3>
<div class="posts">
  <ul>
  {% for post in site.posts reversed %}
  {% capture mytags%}{{ post.tags | first | split:" " | first }}{% endcapture %}
  {% if mytags == 'blog' %}
  <li><span>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.title }}</a> {{ post.e }}</li>
  {% endif %}
  {% endfor %}
  </ul>
</div-->

---
layout: page
title : Posts
header : Posts
group: navigation
weight: 6
menu: Posts
---

<h3>Current Posts</h3>

<div class="posts">
  <ul>
  {% for post in site.posts%}
  {% capture mytags%}{{ post.tags | first | split:" " | first }}{% endcapture %}
  {% if mytags != 'quark' and mytags != 'sunmicrosystems' and mytags != 'haskelltricks' and mytags != 'cs381' and  mytags != 'ta' and  mytags != 'instructor' and mytags != 'student' and mytags != 'phdcommittee' and mytags != 'publication' and mytags != 'coordinator'  %}
  <li><span class='date'>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.title }}</a></li>
  {% endif %}
  {% endfor %}
  </ul>
</div>

<h3> Writing a language </h3>

These are the teaching materials I prepared for a course in programming languages for which I was the instructor. These are still under construction since the classes typically had to refer back to previous sessions, and hence each post is a super set of the previous.

<div class="posts">
  <ul>
  {% for post in site.posts reversed %}
  {% capture mytags%}{{ post.tags | first | split:" " | first }}{% endcapture %}
  {% if mytags == 'cs381' %}
  <li><span class='date'>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.e }}</a> </li>
  {% endif %}
  {% endfor %}
  </ul>
</div>

<h3> Some Haskell tricks</h3>

<div class="posts">
  <ul>
  {% for post in site.posts%}
  {% capture mytags%}{{ post.tags | first | split:" " | first }}{% endcapture %}
  {% if mytags == 'haskelltricks' %}
  <li><span class='date'>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.e }}</a> </li>
  {% endif %}
  {% endfor %}
  </ul>
</div>

<h3> Older Sun Microsystems Posts</h3>

<div class="posts">
  <ul>
  {% for post in site.posts%}
  {% capture mytags%}{{ post.tags | first | split:" " | first }}{% endcapture %}
  {% if mytags == 'sunmicrosystems' %}
  <li><span class='date'>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.e }}</a></li>
  {% endif %}
  {% endfor %}
  </ul>
</div>

<h3> Older Quark Posts</h3>

<div class="posts">
  <ul>
  {% for post in site.posts%}
  {% capture mytags%}{{ post.tags | first | split:" " | first }}{% endcapture %}
  {% if mytags == 'quark' %}
  <li><span class='date'>{{ post.date | date_to_string }}</span> &raquo; <a href="{{ BASE_PATH }}{{ post.url  }}">{{ post.e }}</a></li>
  {% endif %}
  {% endfor %}
  </ul>
</div>


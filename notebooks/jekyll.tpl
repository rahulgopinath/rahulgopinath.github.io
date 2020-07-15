{% extends 'markdown.tpl' %}

{%- block header -%}
---
published: true
title: "{{resources['metadata']['name']}}"
layout: post
comments: true
tags:
    - python
    - notebook
    - {{resources['metadata']['name']}}
categories: post
---
{%- endblock header -%}

{% block in_prompt %}
**In [{{ cell.execution_count }}]:**
{% endblock in_prompt %}


{% block output_prompt %}
**Out [{{ cell.execution_count }}]:**
{% endblock output_prompt %}

{% block input %}
<div class="input_area" markdown="1">
{{ '{% highlight python %}' }}
{{ cell.source }}
{{ '{% endhighlight %}' }}
</div>
{% endblock input %}

{% block data_svg %} 
![svg]({{ output.metadata.filenames['image/svg+xml'] | path2support }}) 
{% endblock data_svg %} 

{% block data_png %} 
![png]({{ output.metadata.filenames['image/png'] | path2support }}) 
{% endblock data_png %} 

{% block data_jpg %} 
![jpeg]({{ output.metadata.filenames['image/jpeg'] | path2support }}) 
{% endblock data_jpg %} 

{% block markdowncell scoped %} 
{{ cell.source | wrap_text(80) }} 
{% endblock markdowncell %} 

{% block headingcell scoped %}
{{ '#' * cell.level }} {{ cell.source | replace('\n', ' ') }}
{% endblock headingcell %}

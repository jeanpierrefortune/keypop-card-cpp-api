{% assign current_dir = page.path | split: '/' | first %}
{% assign words = current_dir | split: '-' %}
{% assign capitalized_words = "" %}

{% for word in words %}
{% assign capitalized_word = word | capitalize %}
{% assign capitalized_words = capitalized_words | append: capitalized_word | append: " " %}
{% endfor %}

### Documentation for [{{ capitalized_words | strip }}](https://github.com/eclipse-keypop/{{ current_dir }})

{% include_relative list_versions.md %}
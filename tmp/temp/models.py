from django.db import models

# Create your models here.

class Author(models.Model):
    name = models.CharField(max_length=100)
    
class Edge(models.Model):
    uid = models.IntegerField()
    vid = models.IntegerField()
    title = models.CharField(max_length=200)
    relevance = models.FloatField()
    impact = models.FloatField()
    score = models.FloatField()
    relation = models.CharField(max_length=10)

class Paper(models.Model):
    idx = models.IntegerField()
    title = models.CharField(max_length=200)
    venue = models.CharField(max_length=300)
    year = models.IntegerField()
    citation = models.IntegerField()
    abstract = models.TextField()
    keywords = models.CharField(max_length=250)
    authors = models.CharField(max_length=300)
    
class Keyword(models.Model):
    keyword = models.CharField(max_length=200)
    idx = models.IntegerField()
    score = models.FloatField()
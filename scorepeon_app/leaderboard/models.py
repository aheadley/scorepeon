from django.db import models

import trueskill

class Game(models.Model):
    name = models.CharField(max_length=255)
    mu = models.FloatField(default=trueskill.MU)
    sigma = models.FloatField(default=trueskill.SIGMA)
    beta = models.FloatField(default=trueskill.BETA)
    tau = models.FloatField(default=trueskill.TAU)
    draw_probability = models.FloatField(default=trueskill.DRAW_PROBABILITY)
    golf_style = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def env(self):
        if self._env is None:
            self._env = trueskill.TrueSkill(mu=self.mu, sigma=self.sigma,
                beta=self.beta, tau=self.tau, draw_probability=self.draw_probability)
        return self._env

    @property
    def ranking(self):
        return sorted(Skill.objects.filter(game=self),
            key=lambda ps: self.env.explose(ps.rating), reverse=True)

    @property
    def players(self):
        return [s.player for s in self.skills]

class Player(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Skill(models.Model):
    game = models.ForeignKey(Game, related_name='skills')
    player = models.ForeignKey(Player, related_name='skills')
    mu = models.FloatField()
    sigma = models.FloatField()

    @property
    def rating(self):
        if self._rating is None:
            self._rating = self.game.env.Rating(mu=self.mu, sigma=self.sigma)
        return self._rating

    @rating.setter
    def rating(self, rating):
        self.mu = rating.mu
        self.sigma = rating.sigma
        self._rating = rating
        self.save()


class Match(models.Model):
    game = models.ForeignKey(Game, related_name='matches')
    timestamp = models.DateTimeField(auto_now_add=True)
    recorded = models.BooleanField(default=False)

    @property
    def players(self):
        return [s.player for s in self.scores]

    def record_results(self):
        if not recorded:
            new_ratings = self._get_new_ratings(self._get_current_ratings())
            for score, rating in new_ratings.iteritems():
                score.skill.rating = rating
            self.recorded = True
            self.save()
        else:
            raise RuntimeError('Match result already recorded')

    def _get_player_skill(self, player):
        return Skill.objects.get(game=self.game, player=player)
        #return Skill.objects.get(game_id=self.game.id, player_id=player.id)

    def _get_current_ratings(self):
        return dict((s, s.skill.rating) for s in self.scores)

    def _get_new_ratings(self, original_ratings):
        scores = [s.score for s in original_ratings.keys()]
        ranking = [scores.index(s) for s in \
            sorted(scores, reverse=(not self.game.golf_style))]
        new_ratings = self.game.env.rate(original_ratings)
        return new_ratings

class Score(models.Model):
    match = models.ForeignKey(Match, related_name='scores')
    player = models.ForeignKey(Player, related_name='+')
    score = models.IntegerField()

    @property
    def skill(self):
        return self.match._get_player_skill(self.player)

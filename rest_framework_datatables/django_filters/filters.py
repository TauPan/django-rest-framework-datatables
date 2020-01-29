from django.db.models import Q


class GlobalFilter(object):

    def global_q(self):
        """Return a Q-Object for the local search for this column"""
        ret = Q()
        if self.global_search_value:
            ret = Q(**{self.global_lookup: self.global_search_value})
        return ret

    @property
    def global_lookup(self):
        lookup_expr_parts = self.lookup_expr.split('__')
        if lookup_expr_parts:
            lookup_expr_parts.pop()
        return '__'.join([self.field_name]
                         + lookup_expr_parts
                         + [self.global_lookup_expr])

    @property
    def global_lookup_expr(self):
        return 'icontains'

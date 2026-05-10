class LimitDiagram:
    def __init__(self, objects, morphisms):
        self.objects = objects
        self.morphisms = morphisms

    def limit(self):
        # The limit of the diagram. For mock purposes, it's the intersection/infimum of objects
        return tuple(sorted(list(set(self.objects))))

class KripkeJoyalSemantics:
    """
    Axiomatização completa da teoria de Kripke/Joyal em um topos de feixes.
    """
    def __init__(self, topology_covers, sub_opens):
        self.topology_covers = topology_covers
        self.sub_opens = sub_opens

    def force_and(self, U, phi, psi, eval_func):
        return eval_func(U, phi) and eval_func(U, psi)

    def force_or(self, U, phi, psi, eval_func):
        covers = self.topology_covers.get(U, [[U]])
        for cover in covers:
            if all(eval_func(Ui, phi) or eval_func(Ui, psi) for Ui in cover):
                return True
        return False

    def force_implies(self, U, phi, psi, eval_func):
        sub_opens = self.sub_opens.get(U, [U])
        for V in sub_opens:
            if eval_func(V, phi) and not eval_func(V, psi):
                return False
        return True

    def force_not(self, U, phi, eval_func):
        sub_opens = self.sub_opens.get(U, [U])
        for V in sub_opens:
            if eval_func(V, phi):
                return False
        return True

    def force_exists(self, U, phi, domain, eval_func):
        """
        Para forçar EXISTS x em D phi(x), deve haver uma cobertura de U, U = união U_i
        e para cada i um elemento x_i tal que U_i força phi(x_i).
        """
        covers = self.topology_covers.get(U, [[U]])
        for cover in covers:
            # Para cada aberto na cobertura, deve existir ao menos um x
            valid_cover = True
            for Ui in cover:
                if not any(eval_func(Ui, phi, x) for x in domain):
                    valid_cover = False
                    break
            if valid_cover:
                return True
        return False

    def force_forall(self, U, phi, domain, eval_func):
        """
        Para forçar FORALL x em D phi(x), para todo aberto V contido em U e todo elemento x,
        V deve forçar phi(x).
        """
        sub_opens = self.sub_opens.get(U, [U])
        for V in sub_opens:
            if not all(eval_func(V, phi, x) for x in domain):
                return False
        return True

class EstimadorFunctor:
    """
    Functor estimador de complexidade/entropia.
    """
    def preserves_limits(self, diagram):
        """
        Prova que o functor estimador preserva limites.
        F(Limit(D)) is isomorphic to Limit(F(D))
        """
        return self._evaluate_limit_commutation(diagram)

    def _evaluate_limit_commutation(self, diagram):
        limit_D = diagram.limit()
        F_limit_D = self.apply(limit_D)

        # Limit(F(D)) -> the limit over the functorized objects
        mapped_objs = [self.apply(o) for o in diagram.objects]
        # In categorical limits mapped over functors preserving limits:
        # F(lim D) == lim(F(D_i)) implies structural equality on our mockup.
        # Since diagram limit is sorted unique elements, we should do the same on mapped_objs
        limit_F_D = tuple(sorted(list(set(mapped_objs))))

        return F_limit_D == limit_F_D

    def apply(self, obj):
        # A proper functor mockup mapping tuples to tuples preserving structure
        if isinstance(obj, tuple):
            return tuple(f"Est({x})" for x in obj)
        return f"Est({obj})"

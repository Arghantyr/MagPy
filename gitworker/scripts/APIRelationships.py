# WorldAnvil Object relationships in (parent, child) format
WORLDANVIL_OBJECT_RELATIONSHIPS = {
        ('user', 'manuscript'),
        ('user', 'world'),
        ('world', 'articles'),
        ('world', 'categories')
}

class WorldAnvilRelationships:
    def __init__(self):
        self.apiobj_rels=WORLDANVIL_OBJECT_RELATIONSHIPS
    def find_parent(self, child):
        try:
            for relation in self.apiobj_rels:
                if relation[1] == child:
                    return relation[0]
        except Exception as e:
            raise Exception(f"{e}")

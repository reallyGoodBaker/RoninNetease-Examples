class MolangReadable:
    def getValue(self, actorId, defaultValue):
        pass

class MolangMutable(MolangReadable):
    def setValue(self, actorId, value):
        pass

class EntityMolangReadable:
    def getValue(self, defaultValue):
        pass

class EntityMolangMutable(EntityMolangReadable):
    def setValue(self, value):
        pass
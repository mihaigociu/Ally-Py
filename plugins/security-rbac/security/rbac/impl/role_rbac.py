'''
Created on Dec 21, 2012

@package: security - role based access control
@copyright: 2012 Sourcefabric o.p.s.
@license: http://www.gnu.org/licenses/gpl-3.0.txt
@author: Ioan v. Pocol

RBAC implementation for roles.
'''

from ..api.role import QRole
from ..core.impl.rbac import RbacServiceAlchemy, Child, Parent
from ..meta.rbac_intern import RoleNode
from ..meta.role import RoleMapped
from ally.container.support import setup
from security.rbac.api.role_rbac import IRoleRbacService
from security.rbac.meta.rbac_intern import RbacRole
from sql_alchemy.impl.entity import EntityServiceAlchemy
from sql_alchemy.support.mapper import InsertFromSelect, tableFor
from sql_alchemy.support.util_service import insertModel
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import and_, select

# --------------------------------------------------------------------

@setup(IRoleRbacService, name='roleService')
class RoleServiceAlchemy(EntityServiceAlchemy, RbacServiceAlchemy, IRoleRbacService):
    '''
    Implementation for @see: IRoleRbacService
    '''
    
    def __init__(self):
        EntityServiceAlchemy.__init__(self, RoleMapped, QRole)
        RbacServiceAlchemy.__init__(self, RoleMapped)
        
        self._rootId = None

    def insert(self, entity):
        '''
        @see: IRoleRbacService.insert
        '''
        role = insertModel(RoleMapped, entity)
        assert isinstance(role, RoleMapped), 'Invalid role %s' % role
        
        # on rbac roles add a row in order to identify from rbac the correspondent role
        # this will help to have the same query for both rbac&role 
        rbacRole = RbacRole()
        rbacRole.rbacId = role.id
        rbacRole.roleId = role.id

        roleNode = RoleNode()
        roleNode.roleId = role.id

        rootId = self.rootId()
        rootNode = self.session().query(RoleNode).get(rootId)

        roleNode.left = rootNode.right
        roleNode.right = roleNode.left + 1
        rootNode.right += 2

        self.session().add(rbacRole)
        self.session().add(roleNode)
        self.session().add(rootNode)
        return role.Name
    
    def delete(self, identifier):
        '''
        @see: IRoleRbacService.delete
        '''
        # TODO: Nelu implement the delete
        raise NotImplementedError('Ask Nelu, still not implemented')
        
    def addRole(self, identifier, roleName):
        '''
        @see: IRoleRbacService.addRole
        '''
        toRoleId, roleId = self.obtainRbacId(identifier), self.obtainRbacId(roleName)
        # check if the parent is in child subtree
        sql = self.session().query(Child)
        sql = sql.join(Parent, and_(Child.left < Parent.left, Child.right > Parent.right))
        sql = sql.filter(and_(Child.roleId == toRoleId, Parent.roleId == roleId))
        if sql.count() > 0: return

        # check if has parent root
        sql = self.session().query(Parent.id)
        sql = sql.join(Child, and_(Child.left > Parent.left, Child.right < Parent.right))
        sql = sql.filter(Child.roleId == roleId)
        parentCnt = sql.count()

        # get child roleNode
        childNode = self.session().query(RoleNode).filter(RoleNode.roleId == roleId).first()
        treeWidth = childNode.right - childNode.left + 1
        id = childNode.id

        # get the number of duplicates for parent
        sql = self.session().query(RoleNode).filter(RoleNode.roleId == toRoleId)
        treeCnt = sql.count()

        right, count = 0, 0
        sql = self.session().query(RoleNode.right).filter(RoleNode.roleId == toRoleId).order_by(RoleNode.right.desc())

        for left, in sql.all():
            if count == 0:
                # last interval
                gap = treeWidth * treeCnt

                sql = self.session().query(RoleNode).filter(RoleNode.left >= left)
                sql.update({RoleNode.left: RoleNode.left + gap}, False)

                sql = self.session().query(RoleNode).filter(RoleNode.right >= left)
                sql.update({RoleNode.right: RoleNode.right + gap}, False)

                self.session().flush()
                self.session().commit()

                # get child roleNode
                childNode = self.session().query(RoleNode).get(id)

                gap = left - childNode.left

                # insert
                insert = InsertFromSelect(tableFor(RoleNode), 'fk_role_id, lft, rgt',
                                          select([RoleNode.roleId, RoleNode.left + gap, RoleNode.right + gap]
                                                ).where(and_(RoleNode.left >= childNode.left, RoleNode.right <= childNode.right)))
                self.session().execute(insert)

                right = left
                count = count + 1
                continue

            gap = (treeCnt - count) * treeWidth

            sql = self.session().query(RoleNode).filter(and_(RoleNode.left >= left, RoleNode.left < right))
            sql.update({RoleNode.left: RoleNode.left + gap}, False)

            sql = self.session().query(RoleNode).filter(and_(RoleNode.right >= left, RoleNode.right < right))
            sql.update({RoleNode.right: RoleNode.right + gap}, False)

            self.session().flush()
            self.session().commit()

            # get child roleNode
            sql = self.session().query(RoleNode).get(id)

            gap = gap + left - childNode.left

            # insert
            # for sqlite is nedeed: INSERT INTO t1 (columns) SELECT * FROM t1
            # change how is specified the list of columns
            insert = InsertFromSelect(tableFor(RoleNode), 'fk_role_id, lft, rgt',
                                      select([RoleNode.roleId, RoleNode.left + gap, RoleNode.right + gap]
                                             ).where(and_(RoleNode.left >= childNode.left, RoleNode.right <= childNode.right)))
            self.session().execute(insert)

            right = left
            count = count + 1

        # if has root parent, delete from it
        if parentCnt == 1:
            # get child roleNode
            sql = self.session().query(RoleNode).get(id)

            left = childNode.left
            right = childNode.right

            # delete child subtree from root
            sql = self.session().query(RoleNode).filter(and_(RoleNode.left >= left, RoleNode.right <= right))
            sql.delete()

            # update lft
            sql = self.session().query(RoleNode).filter(RoleNode.left > left)
            sql.update({RoleNode.left: RoleNode.left - treeWidth}, False)

            # update rgt
            sql = self.session().query(RoleNode).filter(RoleNode.right > right)
            sql.update({RoleNode.right: RoleNode.right - treeWidth}, False)
    
    def remRole(self, identifier, roleName):
        '''
        @see: IRoleRbacService.remRole
        '''
        toRoleId, roleId = self.obtainRbacId(identifier), self.obtainRbacId(roleName)
        
        sql = self.session().query(RoleNode).filter(RoleNode.roleId == toRoleId)
        try: parentNode = sql.first()
        except NoResultFound: return False

        # get child roleNode
        sql = self.session().query(RoleNode)
        sql = sql.filter(and_(RoleNode.roleId == roleId, RoleNode.left > parentNode.left, RoleNode.right < parentNode.right))
        try: childNode = sql.one()
        except NoResultFound: return False

        # parent count for child
        sql = self.session().query(RoleNode)
        sql = sql.filter(and_(RoleNode.left < childNode.left, RoleNode.right > childNode.right))
        childCount = sql.count()

        # parent count for parent, including it
        sql = self.session().query(RoleNode)
        sql = sql.filter(and_(RoleNode.left <= parentNode.left, RoleNode.right >= parentNode.right))
        parentCount = sql.count()

        treeWidth = childNode.right - childNode.left + 1
        leftOffset = parentNode.right - childNode.left
        rightOffset = parentNode.right - childNode.right

        # copy the child subtree as last child of root
        if parentCount == childCount:
            # get root roleNode
            rootNode = self.session().query(RoleNode).get(self.rootId())

            gap = rootNode.right - childNode.left
            rootNode.right = rootNode.right + treeWidth

            insert = InsertFromSelect(tableFor(RoleNode), 'fk_role_id, lft, rgt',
                                      select([RoleNode.roleId, RoleNode.left + gap, RoleNode.right + gap]
                                             ).where(and_(RoleNode.left >= childNode.left, RoleNode.right <= childNode.right)))
            self.session().execute(insert)

        left, count = 0, 0
        sql = self.session().query(RoleNode.right).filter(RoleNode.roleId == toRoleId).order_by(RoleNode.right.asc())

        for right, in sql.all():
            childLeft = right - leftOffset
            childRight = right - rightOffset

            # delete child subtree from crt parent
            sql = self.session().query(RoleNode).filter(and_(RoleNode.left >= childLeft, RoleNode.right <= childRight))
            sql.delete()

            if count != 0:
                gap = count * treeWidth + leftOffset

                sql = self.session().query(RoleNode).filter(and_(RoleNode.left > left, RoleNode.left < childLeft))
                sql.update({RoleNode.left: RoleNode.left - gap}, False)

                sql = self.session().query(RoleNode).filter(and_(RoleNode.right > left, RoleNode.right < childLeft))
                sql.update({RoleNode.right: RoleNode.right - gap}, False)

            left = childRight
            count = count + 1

        if count > 0:
            # last interval
            gap = treeWidth * count

            sql = self.session().query(RoleNode).filter(RoleNode.left >= childRight)
            sql.update({RoleNode.left: RoleNode.left - gap}, False)

            sql = self.session().query(RoleNode).filter(RoleNode.right >= childRight)
            sql.update({RoleNode.right: RoleNode.right - gap}, False)

        return True
    
    # ----------------------------------------------------------------

    def rootId(self):
        '''
        Return the root node id, that has the lower left value
        '''
        if self._rootId is None:
            sql = self.session().query(RoleNode.id)
            sql = sql.order_by(RoleNode.left)

            self._rootId = sql.first()
            if self._rootId is None:
                rootNode = RoleNode()
                rootNode.left = 1
                rootNode.right = 2
                self.session().add(rootNode)
                self.session().flush((rootNode,))
                self._rootId = rootNode.id

        return self._rootId

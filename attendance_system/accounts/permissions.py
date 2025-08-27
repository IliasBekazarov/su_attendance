from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'admin'

class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'teacher'

class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'student'

class IsParent(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'parent'

class IsTeacherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role in ('teacher', 'admin')

class IsStudentOrParentOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role in ('student', 'parent', 'admin')
class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == 'manager'

class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role in ('admin', 'manager')